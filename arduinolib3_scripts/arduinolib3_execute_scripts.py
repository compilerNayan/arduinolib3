"""
Script to execute client file processing.
This script calls the arduinolib1 serializer script to process Serializable macro.
"""

import os
import sys
import importlib.util
from pathlib import Path


def find_library_scripts(scripts_dir_name):
    """
    Find a library scripts directory by searching from current directory and project directory.
    
    Args:
        scripts_dir_name: Name of the scripts directory to find (e.g., "arduinolib1_scripts")
    
    Returns:
        Path: Path to the scripts directory, or None if not found
    """
    # Derive library source directory name from scripts directory name
    # e.g., "arduinolib1_scripts" -> "arduinolib1-src"
    if scripts_dir_name.endswith("_scripts"):
        lib_name = scripts_dir_name[:-8]  # Remove "_scripts" suffix
        lib_src_name = f"{lib_name}-src"
    else:
        # Fallback: assume scripts_dir_name is the library name
        lib_src_name = f"{scripts_dir_name}-src"
    
    search_paths = []
    
    # Add current working directory
    cwd = Path(os.getcwd())
    search_paths.append(cwd)
    
    # Check build/_deps from current working directory (in case we're in a build directory)
    cwd_build_deps = cwd / "_deps" / lib_src_name / scripts_dir_name
    if cwd_build_deps.exists() and cwd_build_deps.is_dir():
        debug_print(f"✓ Found {scripts_dir_name} (CMake from CWD build): {cwd_build_deps}")
        return cwd_build_deps
    
    # Also check if CWD is a build directory, look for _deps
    if cwd.name == "build" or "_deps" in str(cwd):
        deps_dir = cwd / "_deps" / lib_src_name / scripts_dir_name
        if deps_dir.exists() and deps_dir.is_dir():
            debug_print(f"✓ Found {scripts_dir_name} (CMake from CWD _deps): {deps_dir}")
            return deps_dir
    
    # Add project directory if available
    project_dir = os.environ.get("CMAKE_PROJECT_DIR") or os.environ.get("PROJECT_DIR")
    if project_dir:
        project_path = Path(project_dir)
        search_paths.append(project_path)
        
        # Check build/_deps/{lib_src_name}/{scripts_dir_name} from project directory
        build_deps = project_path / "build" / "_deps" / lib_src_name / scripts_dir_name
        if build_deps.exists() and build_deps.is_dir():
            debug_print(f"✓ Found {scripts_dir_name} (CMake from project): {build_deps}")
            return build_deps
    
    # Add library directory (parent of arduinolib3_scripts)
    current_file = Path(__file__).resolve()
    library_scripts_dir = current_file.parent
    library_dir = library_scripts_dir.parent
    search_paths.append(library_dir)
    
    # If we're in a CMake build, check sibling directory ({lib_src_name} next to arduinolib3-src)
    if "arduinolib3-src" in str(library_dir) or "_deps" in str(library_dir):
        # We're in a CMake FetchContent location, check sibling
        parent_deps = library_dir.parent
        if parent_deps.exists() and parent_deps.name == "_deps":
            lib_src = parent_deps / lib_src_name / scripts_dir_name
            if lib_src.exists() and lib_src.is_dir():
                debug_print(f"✓ Found {scripts_dir_name} (CMake sibling): {lib_src}")
                return lib_src
            # Also check if {lib_src_name} exists but scripts might be in root
            lib_root = parent_deps / lib_src_name
            if lib_root.exists():
                lib_scripts = lib_root / scripts_dir_name
                if lib_scripts.exists() and lib_scripts.is_dir():
                    debug_print(f"✓ Found {scripts_dir_name} (CMake sibling root): {lib_scripts}")
                    return lib_scripts
    
    # Search in each path and their parent directories
    for start_path in search_paths:
        current = start_path.resolve()
        for _ in range(10):  # Search up to 10 levels
            # Check for {scripts_dir_name} in current directory
            potential = current / scripts_dir_name
            if potential.exists() and potential.is_dir():
                debug_print(f"✓ Found {scripts_dir_name}: {potential}")
                return potential
            
            # Check in build/_deps/{lib_src_name}/ (CMake FetchContent location)
            deps_path = current / "build" / "_deps" / lib_src_name / scripts_dir_name
            if deps_path.exists() and deps_path.is_dir():
                debug_print(f"✓ Found {scripts_dir_name} (CMake): {deps_path}")
                return deps_path
            
            # Check in .pio/libdeps/ (PlatformIO location)
            # Structure: .pio/libdeps/<env>/<library_name>/
            pio_path = current / ".pio" / "libdeps"
            if pio_path.exists():
                # Iterate through environment directories (e.g., esp32dev, native, etc.)
                for env_dir in pio_path.iterdir():
                    if env_dir.is_dir():
                        # Now iterate through libraries in this environment
                        for lib_dir in env_dir.iterdir():
                            if lib_dir.is_dir():
                                lib_scripts_path = lib_dir / scripts_dir_name
                                if lib_scripts_path.exists() and lib_scripts_path.is_dir():
                                    debug_print(f"✓ Found {scripts_dir_name} (PlatformIO): {lib_scripts_path}")
                                    return lib_scripts_path
            
            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent
    
    debug_print(f"Warning: Could not find {scripts_dir_name} directory")
    return None


def execute_scripts(project_dir, library_dir):
    """
    Execute the scripts to process client files.
    Calls the arduinolib1 serializer script (00_process_serializable_classes.py) directly
    and then injects primary key methods.
    
    Args:
        project_dir: Path to the client project root (where platformio.ini is)
        library_dir: Path to the library directory
    """
    # Set project_dir in globals so serializer scripts can access it
    globals()['project_dir'] = project_dir
    globals()['library_dir'] = library_dir
    
    debug_print(f"\nproject_dir: {project_dir}")
    debug_print(f"library_dir: {library_dir}")
    
    # Get serializable macro name from environment or use default
    serializable_macro = os.environ.get("SERIALIZABLE_MACRO", "_Entity")
    globals()['serializable_macro'] = serializable_macro
    
    # Find arduinolib1_scripts directory
    arduinolib1_scripts_dir = find_library_scripts("arduinolib1_scripts")
    
    if not arduinolib1_scripts_dir:
        debug_print("Warning: Could not find arduinolib1_scripts directory. Skipping Serializable processing.")
        return
    
    # Add arduinolib1_scripts to Python path
    sys.path.insert(0, str(arduinolib1_scripts_dir))
    
    # Try to import get_client_files from arduinolib1
    try:
        from arduinolib1_core.arduinolib1_get_client_files import get_client_files
        HAS_GET_CLIENT_FILES = True
    except ImportError:
        debug_print("Warning: Could not import get_client_files from arduinolib1")
        HAS_GET_CLIENT_FILES = False
    
    # List client files if available
    if HAS_GET_CLIENT_FILES:
        if project_dir:
            client_files = get_client_files(project_dir, file_extensions=['.h', '.cpp'])
            debug_print(f"\nFound {len(client_files)} files in client project:")
            debug_print("=" * 60)
            for file in client_files:
                debug_print(file)
            debug_print("=" * 60)
        
        if library_dir:
            library_files = get_client_files(library_dir, skip_exclusions=True)
            debug_print(f"\nFound {len(library_files)} files in library:")
            debug_print("=" * 60)
            for file in library_files:
                debug_print(file)
            debug_print("=" * 60)
    
    # FIRST: Inject primary key methods BEFORE serializer marks the @Entity annotation as processed
    # This ensures we can find the @Entity annotation before it gets marked as processed
    debug_print(f"\n{'=' * 60}")
    debug_print("🚀 Injecting primary key methods for classes with @Id fields (before serializer)...")
    debug_print(f"{'=' * 60}\n")
    
    try:
        # Add arduinolib3_scripts to path
        current_file = Path(__file__).resolve()
        arduinolib3_scripts_dir = current_file.parent
        sys.path.insert(0, str(arduinolib3_scripts_dir))
        
        from arduinolib3_core.inject_primary_key_methods import process_file
        
        # Get all client files to process
        if HAS_GET_CLIENT_FILES and project_dir:
            client_files = get_client_files(project_dir, file_extensions=['.h', '.cpp'])
            
            processed_count = 0
            for file_path in client_files:
                try:
                    if process_file(str(file_path), serializable_macro=serializable_macro, dry_run=False):
                        processed_count += 1
                except Exception as e:
                    debug_print(f"Warning: Error processing {file_path}: {e}")
            
            if processed_count > 0:
                debug_print(f"\n✅ Successfully injected primary key methods in {processed_count} file(s)")
            else:
                debug_print("\nℹ️  No files with @Id fields found for primary key injection")
        else:
            debug_print("Warning: Could not get client files for primary key injection")
            
    except ImportError as e:
        debug_print(f"Warning: Could not import inject_primary_key_methods: {e}")
    except Exception as e:
        debug_print(f"Error injecting primary key methods: {e}")
        import traceback
        traceback.print_exc()
    
    # THEN: Run the master serializer script (00_process_serializable_classes.py) from arduinolib1
    # This will mark the @Entity annotation as processed after we've already processed it
    # Find the serializer directory
    try:
        # Get the directory of arduinolib1_scripts
        arduinolib1_scripts_path = Path(arduinolib1_scripts_dir)
        # serializer is in arduinolib1_serializer/
        serializer_dir = arduinolib1_scripts_path / 'arduinolib1_serializer'
    except Exception as e:
        debug_print(f"Error finding serializer directory: {e}")
        serializer_dir = None
    
    if serializer_dir and serializer_dir.exists():
        serializer_script_path = serializer_dir / '00_process_serializable_classes.py'
        if serializer_script_path.exists():
            debug_print(f"\n{'=' * 60}")
            debug_print("Running serializer master script: 00_process_serializable_classes.py")
            debug_print(f"{'=' * 60}\n")
            
            try:
                # Set environment variables so serializer script can access project_dir and library_dir
                if project_dir:
                    os.environ['PROJECT_DIR'] = project_dir
                    os.environ['CMAKE_PROJECT_DIR'] = project_dir
                if library_dir:
                    os.environ['LIBRARY_DIR'] = str(library_dir)
                # Set serializable macro name
                os.environ['SERIALIZABLE_MACRO'] = serializable_macro
                
                # Load and execute the serializer script
                spec = importlib.util.spec_from_file_location("process_serializable_classes", str(serializer_script_path))
                serializer_module = importlib.util.module_from_spec(spec)
                
                # Add serializer directory to path for imports
                sys.path.insert(0, str(serializer_dir))
                
                # Set globals in the module's namespace before execution
                # This ensures the serializer script can access project_dir and library_dir
                serializer_module.__dict__['project_dir'] = project_dir
                serializer_module.__dict__['library_dir'] = library_dir
                serializer_module.__dict__['serializable_macro'] = serializable_macro
                
                # Execute the module (this will run the top-level code)
                spec.loader.exec_module(serializer_module)
                
                # Call the main function if it exists
                if hasattr(serializer_module, 'main'):
                    serializer_module.main()
                elif hasattr(serializer_module, 'process_all_serializable_classes'):
                    serializer_module.process_all_serializable_classes(dry_run=False)
                
                debug_print(f"\n✅ Successfully executed arduinolib1 serializer")
                
            except Exception as e:
                debug_print(f"Error running serializer script: {e}")
                import traceback

# Import debug utility
try:
    from debug_utils import debug_print
except ImportError:
    # Fallback if debug_utils not found - create a no-op function
    def debug_print(*args, **kwargs):
        pass

                traceback.print_exc()
        else:
            debug_print(f"Warning: Serializer script not found at {serializer_script_path}")
    else:
        debug_print(f"Warning: Serializer directory not found at {serializer_dir}")

