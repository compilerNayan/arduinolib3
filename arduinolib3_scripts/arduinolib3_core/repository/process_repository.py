#!/usr/bin/env python3
"""
Script to process repository classes: detect _Repository macro, create implementation,
and add include statement to the original repository file.

This script:
1. Detects _Repository macro in a file
2. Creates the implementation file (UserRepositoryImpl.h)
3. Adds an include statement for the impl file in the original repository file
   (just before the last #endif, or at the end if no #endif exists)
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, str(script_dir))

from detect_repository import detect_repository
from implement_repository import implement_repository, generate_impl_class


def find_last_endif_position(content: str) -> Optional[int]:
    """
    Find the position of the last #endif in the file content.
    
    Args:
        content: File content as string
        
    Returns:
        Line number (1-based) of the last #endif, or None if not found
    """
    lines = content.split('\n')
    last_endif_line = None
    
    # Search from the end
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        # Check for #endif (with optional comment after it)
        # Match patterns like: #endif, #endif // comment, #endif/*comment*/
        if re.match(r'^\s*#endif\s*(//.*|/\*.*\*/)?\s*$', line):
            last_endif_line = i + 1  # 1-based line number
            break
    
    return last_endif_line


def add_include_to_file(file_path: str, include_path: str, dry_run: bool = False) -> bool:
    """
    Add an include statement to the repository file.
    Adds it just before the last #endif, or at the end if no #endif exists.
    
    Args:
        file_path: Path to the repository file to modify
        include_path: Path to include (relative or absolute)
        dry_run: If True, don't actually modify the file
        
    Returns:
        True if include was added (or would be added), False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False
    
    # Check if include already exists
    escaped_include = re.escape(include_path)
    if re.search(rf'#include\s+["<]{escaped_include}[">]', content):
        print(f"⚠️  Include for {include_path} already exists in {file_path}")
        return False
    
    # Find the last #endif
    last_endif_line = find_last_endif_position(content)
    
    lines = content.split('\n')
    include_statement = f'#include "{include_path}"'
    
    if dry_run:
        if last_endif_line:
            print(f"Would add include before line {last_endif_line} (last #endif)")
        else:
            print(f"Would add include at the end of file (no #endif found)")
        print(f"  {include_statement}")
        return True
    
    # Add the include
    if last_endif_line:
        # Insert before the last #endif
        insert_index = last_endif_line - 1  # Convert to 0-based
        lines.insert(insert_index, include_statement)
    else:
        # Add at the end
        lines.append(include_statement)
    
    # Write back to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"✓ Added include to {file_path}: {include_path}")
        return True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False


def convert_repository_annotation_to_processed(file_path: str, dry_run: bool = False) -> bool:
    """
    Convert //@Repository to /*@Repository*/ in the source file.
    This marks the annotation as processed so it won't be processed again.
    
    Args:
        file_path: Path to the repository file to modify
        dry_run: If True, don't actually modify the file
        
    Returns:
        True if annotation was converted (or would be converted), False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False
    
    modified = False
    
    # Pattern to match //@Repository annotation
    annotation_pattern = r'^(\s*)//@Repository\s*$'
    
    # Find and convert //@Repository annotation
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip already processed annotations (/*@Repository*/)
        if re.match(r'^\s*/\*@Repository\*/\s*$', stripped):
            continue
        
        # Check for //@Repository annotation
        match = re.match(annotation_pattern, line)
        if match:
            indent = match.group(1)
            # Convert to /*@Repository*/
            if not dry_run:
                lines[i] = f'{indent}/*@Repository*/\n'
            modified = True
            print(f"✓ Found //@Repository annotation on line {i+1}, converting to /*@Repository*/")
            if dry_run:
                print(f"    Would convert: {stripped} -> /*@Repository*/")
            break
    
    if not modified:
        # Check if already processed
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r'^\s*/\*@Repository\*/\s*$', stripped):
                print(f"✓ //@Repository annotation already processed in {file_path} (line {i+1})")
                return True
        # Debug: print first few lines to see what we're looking at
        print(f"⚠️  //@Repository annotation not found in {file_path}")
        print(f"   First 15 lines of file:")
        for j, l in enumerate(lines[:15], 1):
            print(f"   {j:2}: {repr(l)}")
        return False
    
    if dry_run:
        print(f"Would convert //@Repository to /*@Repository*/ in {file_path}")
        return True
    
    # Write back to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✓ Converted //@Repository to /*@Repository*/ in {file_path}")
        return True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False


def calculate_include_path(source_file_path: str, impl_file_path: str) -> str:
    """
    Calculate the absolute path for the implementation file.
    
    Args:
        source_file_path: Path to the source repository file
        impl_file_path: Path to the generated implementation file
        
    Returns:
        Absolute include path
    """
    impl_path = Path(impl_file_path).resolve()
    
    # Return absolute path
    return str(impl_path)


def process_repository(file_path: str, library_dir: str, dry_run: bool = False) -> bool:
    """
    Process a repository file: detect macro, create implementation, and add include.
    
    Args:
        file_path: Path to the source file to check
        library_dir: Path to the library directory (where src/repository folder should be)
        dry_run: If True, don't actually create or modify files
        
    Returns:
        True if repository was processed successfully, False otherwise
    """
    # Step 1: Detect repository in the file
    result = detect_repository(file_path)
    
    if not result:
        return False
    
    if len(result) == 4:
        class_name, entity_type, id_type, is_templated = result
        if is_templated:
            print(f"🔍 Found templated repository: {class_name}<{entity_type}, {id_type}> in {file_path}")
        else:
            print(f"🔍 Found non-templated repository: {class_name}<{entity_type}, {id_type}> in {file_path}")
    else:
        # Backward compatibility
        class_name, entity_type, id_type = result
        is_templated = True
        print(f"🔍 Found repository: {class_name}<{entity_type}, {id_type}> in {file_path}")
    
    # Step 2: Create the implementation file (or check if it exists)
    repository_dir = Path(library_dir) / "src" / "repository"
    impl_file_name = f"{class_name}Impl.h"
    impl_file_path = repository_dir / impl_file_name
    
    # Try to create the implementation file
    impl_created = implement_repository(file_path, library_dir, dry_run)
    
    # Check if implementation file exists (either newly created or already existed)
    if not dry_run and not impl_file_path.exists():
        print(f"⚠️  Implementation file was not created: {impl_file_path}")
        return False
    
    # Step 4: Calculate include path (relative from source file to impl file)
    include_path = calculate_include_path(file_path, str(impl_file_path))
    print(f"📝 Calculated include path: {include_path}")
    
    # Step 5: Add include to the original repository file
    include_added = add_include_to_file(file_path, include_path, dry_run)
    
    if not include_added:
        print(f"⚠️  Failed to add include for repository {class_name}")
        return False
    
    # Step 6: Convert //@Repository to /*@Repository*/
    annotation_converted = convert_repository_annotation_to_processed(file_path, dry_run)
    
    if include_added and annotation_converted:
        print(f"✅ Successfully processed repository {class_name}")
        return True
    else:
        print(f"⚠️  Repository {class_name} processed but annotation conversion failed")
        return include_added  # Return True if at least include was added


def main():
    """Main function to handle command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process repository classes: detect _Repository macro, create implementation, and add include"
    )
    parser.add_argument(
        "file_path",
        help="Path to the C++ file to check"
    )
    parser.add_argument(
        "--library-dir",
        required=True,
        help="Path to the library directory (where src/repository folder should be)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created/modified without actually doing it"
    )
    
    args = parser.parse_args()
    
    success = process_repository(args.file_path, args.library_dir, args.dry_run)
    
    return 0 if success else 1


# Export functions for other scripts to import
__all__ = [
    'process_repository',
    'add_include_to_file',
    'calculate_include_path',
    'main'
]


if __name__ == "__main__":
    exit(main())

