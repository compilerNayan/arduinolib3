#!/usr/bin/env python3
"""
00 Process Entity Classes Script

Orchestrator script that processes all classes with @Entity annotation in client files.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Import get_client_files from parent directory
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

try:
    from get_client_files import get_client_files
except ImportError:
    get_client_files = None

# Import the serializer scripts
sys.path.insert(0, script_dir)

spec_s1 = importlib.util.spec_from_file_location("S1_check_dto_macro", os.path.join(script_dir, "S1_check_dto_macro.py"))
S1_check_dto_macro = importlib.util.module_from_spec(spec_s1)
spec_s1.loader.exec_module(S1_check_dto_macro)

spec_s3 = importlib.util.spec_from_file_location("S3_inject_serialization", os.path.join(script_dir, "S3_inject_serialization.py"))
S3_inject_serialization = importlib.util.module_from_spec(spec_s3)
spec_s3.loader.exec_module(S3_inject_serialization)


def discover_all_libraries(project_dir):
    """Discover all library directories in build/_deps/ (CMake) and .pio/libdeps/ (PlatformIO)."""
    libraries = []
    seen_libraries = set()
    
    if not project_dir:
        return libraries
    
    project_path = Path(project_dir).resolve()
    
    build_deps = project_path / "build" / "_deps"
    
    if build_deps.exists() and build_deps.is_dir():
        for lib_dir in build_deps.iterdir():
            if lib_dir.is_dir() and not lib_dir.name.startswith("."):
                lib_name = lib_dir.name
                
                if lib_name.endswith("-src"):
                    lib_root = lib_dir.resolve()
                    lib_path_str = str(lib_root)
                    if lib_path_str not in seen_libraries:
                        seen_libraries.add(lib_path_str)
                        libraries.append(lib_root)
                elif (lib_dir / "src").exists() and (lib_dir / "src").is_dir():
                    lib_root = lib_dir.resolve()
                    lib_path_str = str(lib_root)
                    if lib_path_str not in seen_libraries:
                        seen_libraries.add(lib_path_str)
                        libraries.append(lib_root)
    
    pio_libdeps = project_path / ".pio" / "libdeps"
    
    if pio_libdeps.exists() and pio_libdeps.is_dir():
        for env_dir in pio_libdeps.iterdir():
            if env_dir.is_dir():
                for lib_dir in env_dir.iterdir():
                    if lib_dir.is_dir():
                        lib_root = lib_dir.resolve()
                        lib_path_str = str(lib_root)
                        
                        if (lib_root / "src").exists() and (lib_root / "src").is_dir():
                            if lib_path_str not in seen_libraries:
                                seen_libraries.add(lib_path_str)
                                libraries.append(lib_root)
    
    return libraries


def process_all_serializable_classes(dry_run=False, serializable_macro=None):
    """Process all client files that contain classes with @Entity annotation."""
    if serializable_macro is None:
        if 'serializable_macro' in globals():
            serializable_macro = globals()['serializable_macro']
        elif 'SERIALIZABLE_MACRO' in os.environ:
            serializable_macro = os.environ['SERIALIZABLE_MACRO']
        else:
            serializable_macro = "_Entity"
    
    project_dir = None
    if 'project_dir' in globals():
        project_dir = globals()['project_dir']
    elif 'PROJECT_DIR' in os.environ:
        project_dir = os.environ['PROJECT_DIR']
    elif 'CMAKE_PROJECT_DIR' in os.environ:
        project_dir = os.environ['CMAKE_PROJECT_DIR']
    
    if not project_dir:
        return 0
    
    if get_client_files is None:
        return 0
    
    all_libraries = discover_all_libraries(project_dir)
    
    header_files = []
    
    try:
        project_files = get_client_files(project_dir, file_extensions=['.h', '.hpp'])
        header_files.extend(project_files)
    except Exception as e:
        pass
    
    for lib_dir in all_libraries:
        try:
            lib_files = get_client_files(str(lib_dir), skip_exclusions=True, file_extensions=['.h', '.hpp'])
            header_files.extend(lib_files)
        except Exception as e:
            pass
    
    if not header_files:
        return 0
    
    processed_count = 0
    
    for file_path in header_files:
        if not os.path.exists(file_path):
            continue
        
        dto_info = S1_check_dto_macro.check_dto_macro(file_path, serializable_macro)
        
        if not dto_info or not dto_info.get('has_dto'):
            continue
        
        class_name = dto_info['class_name']
        
        import S2_extract_dto_fields
        spec_s2 = importlib.util.spec_from_file_location("S2_extract_dto_fields", os.path.join(script_dir, "S2_extract_dto_fields.py"))
        S2_extract_dto_fields = importlib.util.module_from_spec(spec_s2)
        spec_s2.loader.exec_module(S2_extract_dto_fields)
        
        fields = S2_extract_dto_fields.extract_all_fields(file_path, class_name)
        
        if not fields:
            pass
        
        optional_fields = [field for field in fields if S3_inject_serialization.is_optional_type(field['type'].strip())]
        non_optional_fields = [field for field in fields if not S3_inject_serialization.is_optional_type(field['type'].strip())]
        
        import S6_discover_validation_macros
        spec_s6 = importlib.util.spec_from_file_location("S6_discover_validation_macros", os.path.join(script_dir, "S6_discover_validation_macros.py"))
        S6_discover_validation_macros = importlib.util.module_from_spec(spec_s6)
        spec_s6.loader.exec_module(S6_discover_validation_macros)
        
        validation_macros = S6_discover_validation_macros.find_validation_macro_definitions(None)
        
        import S7_extract_validation_fields
        spec_s7 = importlib.util.spec_from_file_location("S7_extract_validation_fields", os.path.join(script_dir, "S7_extract_validation_fields.py"))
        S7_extract_validation_fields = importlib.util.module_from_spec(spec_s7)
        spec_s7.loader.exec_module(S7_extract_validation_fields)
        
        validation_fields_by_macro = S7_extract_validation_fields.extract_validation_fields(
            file_path, class_name, validation_macros
        )
        
        methods_code = S3_inject_serialization.generate_serialization_methods(class_name, fields, validation_fields_by_macro)
        
        if not dry_run:
            if optional_fields:
                S3_inject_serialization.add_include_if_needed(file_path, "<optional>")
        
        success = S3_inject_serialization.inject_methods_into_class(file_path, class_name, methods_code, dry_run=dry_run)
        
        if success:
            if not dry_run:
                S3_inject_serialization.comment_dto_macro(file_path, dry_run=False, serializable_macro=serializable_macro)
            processed_count += 1
    
    return processed_count


def main():
    """Main function to process all Entity classes."""
    serializable_macro = None
    if 'serializable_macro' in globals():
        serializable_macro = globals()['serializable_macro']
    elif 'SERIALIZABLE_MACRO' in os.environ:
        serializable_macro = os.environ['SERIALIZABLE_MACRO']
    
    processed_count = process_all_serializable_classes(dry_run=False, serializable_macro=serializable_macro)
    
    return 0


if __name__ == "__main__":
    exit(main())

