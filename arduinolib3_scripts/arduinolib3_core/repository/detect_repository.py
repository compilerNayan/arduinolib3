#!/usr/bin/env python3
"""
Script to detect _Repository macro and extract class information from C++ source files.

Detects patterns:
1. _Repository
   DefineStandardPointers(SomeClass)
   class SomeClass : public CpaRepository<Something, SomethingElse>

2. _Repository
   DefineStandardPointers(SomeClass)
   class SomeClass final : public CpaRepository<Something, SomethingElse>

3. DefineStandardPointers(SomeClass)
   _Repository
   class SomeClass final : public CpaRepository<Something, SomethingElse>

4. DefineStandardPointers(SomeClass)
   _Repository
   class SomeClass : public CpaRepository<Something, SomethingElse>

Returns: class_name, template_param1, template_param2
"""

import re
import sys
from typing import Optional, Tuple


def remove_comments(content: str) -> str:
    """Remove both // and /* */ style comments."""
    # Remove single-line comments
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    
    # Remove multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    return content


def find_repository_macro(content: str) -> bool:
    """Check if _Repository macro is present (not commented)."""
    # Remove comments first
    content_no_comments = remove_comments(content)
    
    # Look for _Repository macro (standalone or with whitespace)
    pattern = r'_Repository\b'
    return bool(re.search(pattern, content_no_comments))


def extract_class_name_from_define_standard_pointers(content: str) -> Optional[str]:
    """Extract class name from DefineStandardPointers(ClassName)."""
    pattern = r'DefineStandardPointers\s*\(\s*(\w+)\s*\)'
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return None


def extract_cpaRepository_info(content: str, class_name: str) -> Optional[Tuple[str, str]]:
    """Extract template parameters from CpaRepository<Type1, Type2>."""
    # Pattern to match: class ClassName (optional final) : public CpaRepository<Type1, Type2>
    # Handle both with and without 'final' keyword
    pattern = rf'class\s+{re.escape(class_name)}\s+(?:final\s+)?:\s*public\s+CpaRepository\s*<\s*([^,<>]+)\s*,\s*([^,<>]+)\s*>'
    
    match = re.search(pattern, content)
    if match:
        type1 = match.group(1).strip()
        type2 = match.group(2).strip()
        return (type1, type2)
    return None


def detect_repository(file_path: str) -> Optional[Tuple[str, str, str]]:
    """
    Detect _Repository macro and extract class information.
    
    Returns: (class_name, template_param1, template_param2) or None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return None
    
    # Check if _Repository macro is present (not commented)
    if not find_repository_macro(content):
        return None
    
    # Extract class name from DefineStandardPointers
    class_name = extract_class_name_from_define_standard_pointers(content)
    if not class_name:
        return None
    
    # Remove comments for class pattern matching (to avoid issues with commented code)
    content_no_comments = remove_comments(content)
    
    # Extract CpaRepository template parameters
    template_params = extract_cpaRepository_info(content_no_comments, class_name)
    if not template_params:
        return None
    
    type1, type2 = template_params
    return (class_name, type1, type2)


def main():
    """Main function to run the script."""
    if len(sys.argv) < 2:
        print("Usage: python detect_repository.py <source_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = detect_repository(file_path)
    
    if result:
        class_name, type1, type2 = result
        print(f"Class: {class_name}")
        print(f"Template Parameter 1: {type1}")
        print(f"Template Parameter 2: {type2}")
        sys.exit(0)
    else:
        print("No _Repository macro found or pattern not matched.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

