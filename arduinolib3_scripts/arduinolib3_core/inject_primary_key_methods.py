#!/usr/bin/env python3
"""
Inject Primary Key Methods Script

This script uses extract_id_fields to find _Id_ fields in a class,
and injects GetPrimaryKey() and GetPrimaryKeyName() methods at the end of the class.
"""

import re
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict

print("Executing arduinolib3_core/inject_primary_key_methods.py")

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_scripts_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_scripts_dir)
sys.path.insert(0, script_dir)

# Import extract_id_fields
try:
    from arduinolib3_core.extract_id_fields import extract_id_fields_from_file, extract_id_fields
    HAS_EXTRACT_ID = True
except ImportError as e:
    print(f"Warning: Could not import extract_id_fields: {e}")
    HAS_EXTRACT_ID = False


def find_class_boundaries(file_path: str, class_name: str) -> Optional[tuple]:
    """
    Find the start and end line numbers of a class definition.
    
    Args:
        file_path: Path to the C++ file
        class_name: Name of the class to find
        
    Returns:
        Tuple of (start_line, end_line) or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    class_start = None
    brace_count = 0
    in_class = False
    
    class_pattern = rf'class\s+{re.escape(class_name)}'
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Skip commented lines
        if stripped_line.startswith('//') or stripped_line.startswith('/*') or stripped_line.startswith('*'):
            continue
        
        # Check for class declaration
        if not in_class and re.search(class_pattern, stripped_line):
            class_start = line_num
            in_class = True
            # Initialize brace count from this line
            brace_count = stripped_line.count('{') - stripped_line.count('}')
        elif in_class:
            # Count braces for subsequent lines
            brace_count += stripped_line.count('{')
            brace_count -= stripped_line.count('}')
        
        if in_class:
            # If braces are balanced and we've closed the class, we're done
            if brace_count == 0:
                return (class_start, line_num)
    
    return None


def generate_primary_key_methods(field_type: str, field_name: str, class_name: str) -> str:
    """
    Generate GetPrimaryKey(), GetPrimaryKeyName(), and GetTableName() methods.
    
    Args:
        field_type: Type of the primary key field
        field_name: Name of the primary key field
        class_name: Name of the class
        
    Returns:
        String containing the method definitions
    """
    methods = []
    
    # GetPrimaryKey() method
    methods.append(f"    inline {field_type} GetPrimaryKey() {{")
    methods.append(f"        return {field_name};")
    methods.append(f"    }}")
    methods.append("")
    
    # GetPrimaryKeyName() method
    methods.append(f"    inline Static StdString GetPrimaryKeyName() {{")
    methods.append(f'        return "{field_name}";')
    methods.append(f"    }}")
    methods.append("")
    
    # GetTableName() method
    methods.append(f"    inline Static StdString GetTableName() {{")
    methods.append(f'        return "{class_name}";')
    methods.append(f"    }}")
    
    return "\n".join(methods)


def inject_primary_key_methods(file_path: str, class_name: str, field_type: str, field_name: str, dry_run: bool = False) -> bool:
    """
    Inject GetPrimaryKey() and GetPrimaryKeyName() methods at the end of a class.
    
    Args:
        file_path: Path to the C++ file
        class_name: Name of the class
        field_type: Type of the primary key field
        field_name: Name of the primary key field
        dry_run: If True, don't actually modify the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    # Find class boundaries
    boundaries = find_class_boundaries(file_path, class_name)
    if not boundaries:
        print(f"Error: Could not find class boundaries for {class_name}")
        return False
    
    start_line, end_line = boundaries
    
    # Find the closing brace line (should be end_line)
    # Look for the line with just "};" or "} ;" or similar patterns
    closing_line_idx = end_line - 1  # Convert to 0-indexed
    
    # Check if methods already exist
    class_lines = lines[start_line - 1:end_line]
    class_content = ''.join(class_lines)
    
    if 'GetPrimaryKey()' in class_content or 'GetTableName()' in class_content:
        print(f"⚠️  Primary key methods already exist in {class_name}, skipping injection")
        return False
    
    # Generate the methods code
    methods_code = generate_primary_key_methods(field_type, field_name, class_name)
    
    # Find the indentation of the closing brace
    closing_line = lines[closing_line_idx]
    # Get indentation from the closing brace line
    indent_match = re.match(r'^(\s*)', closing_line)
    indent = indent_match.group(1) if indent_match else "    "
    
    # Add proper indentation to methods
    indented_methods = []
    for line in methods_code.split('\n'):
        if line.strip():  # Non-empty line
            indented_methods.append(indent + line)
        else:
            indented_methods.append('')
    
    methods_code = '\n'.join(indented_methods)
    
    if dry_run:
        print(f"Would inject the following methods into {class_name} in {file_path}:")
        print("=" * 60)
        print(methods_code)
        print("=" * 60)
        return True
    
    # Insert methods before the closing brace
    # Find the last non-empty, non-comment line before the closing brace
    insert_position = closing_line_idx
    
    # Look backwards from the closing brace to find where to insert
    for i in range(closing_line_idx - 1, start_line - 2, -1):
        stripped = lines[i].strip()
        # Skip empty lines and comments
        if stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
            insert_position = i + 1
            break
    
    # Ensure we have a newline before the methods
    methods_code = '\n' + methods_code
    
    # Convert methods_code to list of lines with newlines
    methods_lines = []
    for line in methods_code.split('\n'):
        methods_lines.append(line + '\n')
    
    # Insert the methods
    lines[insert_position:insert_position] = methods_lines
    
    # Write back to file
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        print(f"✓ Injected GetPrimaryKey() methods into {class_name} in {file_path}")
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False


def convert_id_annotation_to_processed(file_path: str, class_name: str, dry_run: bool = False) -> bool:
    """
    Convert //@Id to /*@Id*/ in a C++ file after processing.
    This marks the annotation as processed so it won't be processed again.
    
    Args:
        file_path: Path to the C++ file to modify
        class_name: Name of the class (to find class boundaries)
        dry_run: If True, don't actually modify the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    # Find class boundaries
    boundaries = find_class_boundaries(file_path, class_name)
    if not boundaries:
        return False
    
    start_line, end_line = boundaries
    modified = False
    
    # Pattern to match //@Id annotation
    id_annotation_pattern = r'^(\s*)//@Id\s*$'
    
    # Only process lines within the class
    for i in range(start_line - 1, end_line):
        if i >= len(lines):
            break
        
        line = lines[i]
        stripped = line.strip()
        
        # Skip already processed annotations
        if re.match(r'^\s*/\*@Id\*/\s*$', stripped):
            continue
        
        # Check if line contains //@Id annotation
        match = re.match(id_annotation_pattern, line)
        if match:
            indent = match.group(1)
            # Convert to /*@Id*/
            if not dry_run:
                lines[i] = f'{indent}/*@Id*/\n'
            modified = True
            if dry_run:
                print(f"    Would convert: {stripped} -> /*@Id*/")
    
    # Write back to file if modifications were made and not dry run
    if modified and not dry_run:
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
            print(f"✓ Converted //@Id to /*@Id*/ in {class_name}")
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False
    elif modified and dry_run:
        print(f"  Would convert //@Id to /*@Id*/ in {class_name}")
        return True
    
    return True


def process_file(file_path: str, serializable_macro: str = "Entity", dry_run: bool = False) -> bool:
    """
    Process a file: extract //@Id fields and inject primary key methods.
    
    Args:
        file_path: Path to the C++ file
        serializable_macro: Name of the Entity annotation (default: "Entity", looks for //@Entity)
        dry_run: If True, don't actually modify the file
        
    Returns:
        True if successful, False otherwise
    """
    if not HAS_EXTRACT_ID:
        print("Error: extract_id_fields module not available")
        return False
    
    # Extract //@Id fields
    result = extract_id_fields_from_file(file_path, serializable_macro)
    
    if not result or not result.get('has_serializable'):
        print(f"File {file_path} does not have //@{serializable_macro} annotation, skipping")
        return False
    
    id_fields = result.get('id_fields', [])
    
    if not id_fields:
        print(f"No //@Id fields found in {result.get('class_name')}, skipping")
        return False
    
    # Use the first //@Id field as the primary key
    # (In a real scenario, you might want to handle composite keys differently)
    primary_key_field = id_fields[0]
    field_type = primary_key_field['type']
    field_name = primary_key_field['name']
    class_name = result['class_name']
    
    print(f"Found primary key field in {class_name}: {field_type} {field_name}")
    
    # Inject the methods
    success = inject_primary_key_methods(file_path, class_name, field_type, field_name, dry_run)
    
    # Convert //@Id to /*@Id*/ after successful injection
    if success and not dry_run:
        convert_id_annotation_to_processed(file_path, class_name, dry_run)
    
    return success


def main():
    """Main function to handle command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Inject GetPrimaryKey() methods into classes with _Id_ fields"
    )
    parser.add_argument(
        "file_path",
        help="Path to the C++ file"
    )
    parser.add_argument(
        "--macro",
        default="Entity",
        help="Name of the Entity annotation to search for (default: Entity, looks for //@Entity)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    
    args = parser.parse_args()
    
    success = process_file(args.file_path, args.macro, args.dry_run)
    
    return 0 if success else 1


# Export functions for other scripts to import
__all__ = [
    'generate_primary_key_methods',
    'inject_primary_key_methods',
    'process_file',
    'main'
]


if __name__ == "__main__":
    exit(main())

