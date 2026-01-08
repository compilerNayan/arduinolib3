#!/usr/bin/env python3
"""
Script to extract variable name from a FindBy method name.

This script takes a method name like "FindByLastName" and extracts
the variable name "lastName" by converting the part after "FindBy"
from PascalCase to camelCase.

Examples:
    FindByLastName -> lastName
    FindByName -> name
    FindByAddress -> address
    FindByFirstName -> firstName

Usage:
    python extract_findby_variable_name.py <method_name>
    
Returns:
    The extracted variable name in camelCase, or None if not a FindBy method
"""

import re
import sys
from typing import Optional


def pascal_to_camel(pascal_case: str) -> str:
    """
    Convert PascalCase to camelCase.
    
    Args:
        pascal_case: String in PascalCase (e.g., "LastName")
        
    Returns:
        String in camelCase (e.g., "lastName")
    """
    if not pascal_case:
        return ""
    
    # If first character is uppercase, make it lowercase
    if pascal_case[0].isupper():
        return pascal_case[0].lower() + pascal_case[1:]
    
    return pascal_case


def extract_findby_variable_name(method_name: str) -> Optional[str]:
    """
    Extract variable name from a FindBy method name.
    
    Args:
        method_name: Method name like "FindByLastName", "FindByName", etc.
        
    Returns:
        Variable name in camelCase (e.g., "lastName", "name"), or None if not a FindBy method
    """
    if not method_name:
        return None
    
    # Pattern to match FindBy methods (case-insensitive)
    # Matches: FindBy, FindByLastName, FindByName, etc.
    pattern = r'^FindBy(.+)$'
    match = re.match(pattern, method_name, re.IGNORECASE)
    
    if not match:
        return None
    
    # Extract the part after "FindBy"
    pascal_case_part = match.group(1)
    
    # Convert to camelCase
    camel_case = pascal_to_camel(pascal_case_part)
    
    return camel_case


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python extract_findby_variable_name.py <method_name>", file=sys.stderr)
        sys.exit(1)
    
    method_name = sys.argv[1]
    variable_name = extract_findby_variable_name(method_name)
    
    if variable_name:
        print(variable_name)
        sys.exit(0)
    else:
        print(f"'{method_name}' is not a FindBy method", file=sys.stderr)
        sys.exit(1)


# Export function for other scripts to import
__all__ = [
    'extract_findby_variable_name',
    'pascal_to_camel',
    'main'
]


if __name__ == "__main__":
    main()

