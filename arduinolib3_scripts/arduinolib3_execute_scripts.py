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
    search_paths.append(Path(os.getcwd()))
    
    # Add project directory if available
    project_dir = os.environ.get("CMAKE_PROJECT_DIR") or os.environ.get("PROJECT_DIR")
    if project_dir:
        project_path = Path(project_dir)
        search_paths.append(project_path)
        
        # Check build/_deps/{lib_src_name}/{scripts_dir_name} from project directory
        build_deps = project_path / "build" / "_deps" / lib_src_name / scripts_dir_name
        if build_deps.exists() and build_deps.is_dir():
            print(f"✓ Found {scripts_dir_name} (CMake from project): {build_deps}")
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
                print(f"✓ Found {scripts_dir_name} (CMake sibling): {lib_src}")
                return lib_src
            # Also check if {lib_src_name} exists but scripts might be in root
            lib_root = parent_deps / lib_src_name
            if lib_root.exists():
                lib_scripts = lib_root / scripts_dir_name
                if lib_scripts.exists() and lib_scripts.is_dir():
                    print(f"✓ Found {scripts_dir_name} (CMake sibling root): {lib_scripts}")
                    return lib_scripts
    
    # Search in each path and their parent directories
    for start_path in search_paths:
        current = start_path.resolve()
        for _ in range(10):  # Search up to 10 levels
            # Check for {scripts_dir_name} in current directory
            potential = current / scripts_dir_name
            if potential.exists() and potential.is_dir():
                print(f"✓ Found {scripts_dir_name}: {potential}")
                return potential
            
            # Check in build/_deps/{lib_src_name}/ (CMake FetchContent location)
            deps_path = current / "build" / "_deps" / lib_src_name / scripts_dir_name
            if deps_path.exists() and deps_path.is_dir():
                print(f"✓ Found {scripts_dir_name} (CMake): {deps_path}")
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
                                    print(f"✓ Found {scripts_dir_name} (PlatformIO): {lib_scripts_path}")
                                    return lib_scripts_path
            
            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent
    
    print(f"Warning: Could not find {scripts_dir_name} directory")
    return None


def execute_scripts(project_dir, library_dir):
    """
    Execute the scripts to process client files.
    Calls the arduinolib1 serializer script to process Serializable macro.
    
    Args:
        project_dir: Path to the client project root (where platformio.ini is)
        library_dir: Path to the library directory
    """
    print(f"\nproject_dir: {project_dir}")
    print(f"library_dir: {library_dir}")
    
    # Find arduinolib1_scripts directory
    arduinolib1_scripts_dir = find_library_scripts("arduinolib1_scripts")
    
    if not arduinolib1_scripts_dir:
        print("Warning: Could not find arduinolib1_scripts directory. Skipping Serializable processing.")
        return
    
    # Add arduinolib1_scripts to Python path
    sys.path.insert(0, str(arduinolib1_scripts_dir))
    
    # Try to import and call arduinolib1_execute_scripts
    try:
        # Import the execute_scripts function from arduinolib1
        from arduinolib1_execute_scripts import execute_scripts as arduinolib1_execute_scripts
        
        # Get serializable macro name from environment or use default
        serializable_macro = os.environ.get("SERIALIZABLE_MACRO", "_Entity")
        
        print(f"\n{'=' * 60}")
        print("🚀 Calling arduinolib1 serializer to process Serializable macro...")
        print(f"{'=' * 60}\n")
        
        # Call the arduinolib1 execute_scripts function
        arduinolib1_execute_scripts(project_dir, library_dir, serializable_macro=serializable_macro)
        
        print(f"\n✅ Successfully called arduinolib1 serializer")
        
    except ImportError as e:
        print(f"Warning: Could not import arduinolib1_execute_scripts: {e}")
        print("         Some features may be unavailable.")
    except Exception as e:
        print(f"Error calling arduinolib1 serializer: {e}")
        import traceback
        traceback.print_exc()

