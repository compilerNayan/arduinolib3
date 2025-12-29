# Print message immediately when script is loaded
print("Hello I am in arduinolib3")

# Import PlatformIO environment first (if available)
env = None
try:
    Import("env")
except NameError:
    # Not running in PlatformIO environment (e.g., running from CMake)
    print("Note: Not running in PlatformIO environment - some features may be limited")
    # Create a mock env object for CMake builds
    class MockEnv:
        def get(self, key, default=None):
            return default
    env = MockEnv()

import sys
import os
from pathlib import Path


def get_library_dir():
    """
    Find the arduinolib3_scripts directory by searching up the directory tree.
    
    Returns:
        Path: Path to the arduinolib3_scripts directory
        
    Raises:
        ImportError: If the directory cannot be found
    """
    cwd = Path(os.getcwd())
    current = cwd
    for _ in range(10):  # Search up to 10 levels
        potential = current / "arduinolib3_scripts"
        if potential.exists() and potential.is_dir():
            print(f"✓ Found library path by searching up directory tree: {potential}")
            return potential
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent
    raise ImportError("Could not find arduinolib3_scripts directory")


def get_current_library_path(project_dir=None):
    """
    Get the full path of the current library (arduinolib3) when included in a client project.
    
    This function finds the library by:
    1. Checking if we're in a CMake FetchContent location (build/_deps/arduinolib3-src)
    2. Checking if we're in a PlatformIO location (.pio/libdeps/)
    3. Using get_library_dir() and getting its parent
    
    Args:
        project_dir: Optional project directory. If None, tries to get from environment.
    
    Returns:
        Path: Full path to the arduinolib3 library root directory, or None if not found
    """
    # Get project directory if not provided
    if project_dir is None:
        project_dir = os.environ.get("CMAKE_PROJECT_DIR") or os.environ.get("PROJECT_DIR")
    
    # First, try to get library scripts directory
    try:
        library_scripts_dir = get_library_dir()
        library_root = library_scripts_dir.parent
        
        # If we're in a CMake FetchContent location, return the resolved path
        if "arduinolib3-src" in str(library_root) or "_deps" in str(library_root):
            return library_root.resolve()
        
        # Otherwise, return the parent of scripts directory
        return library_root.resolve()
    except ImportError:
        pass
    
    # Try to find from project directory's build/_deps
    if project_dir:
        project_path = Path(project_dir)
        build_deps = project_path / "build" / "_deps" / "arduinolib3-src"
        if build_deps.exists() and build_deps.is_dir():
            print(f"✓ Found arduinolib3 library path (CMake from project): {build_deps}")
            return build_deps.resolve()
    
    # Try to find from current working directory's build/_deps
    cwd = Path(os.getcwd())
    if cwd.name == "build" or "_deps" in str(cwd):
        deps_dir = cwd / "_deps" / "arduinolib3-src"
        if deps_dir.exists() and deps_dir.is_dir():
            print(f"✓ Found arduinolib3 library path (CMake from CWD): {deps_dir}")
            return deps_dir.resolve()
    
    # Try PlatformIO location
    current = cwd.resolve()
    for _ in range(10):
        pio_path = current / ".pio" / "libdeps"
        if pio_path.exists() and pio_path.is_dir():
            for env_dir in pio_path.iterdir():
                if env_dir.is_dir():
                    for lib_dir in env_dir.iterdir():
                        if lib_dir.is_dir() and "arduinolib3" in lib_dir.name.lower():
                            print(f"✓ Found arduinolib3 library path (PlatformIO): {lib_dir}")
                            return lib_dir.resolve()
        
        parent = current.parent
        if parent == current:
            break
        current = parent
    
    print("Warning: Could not determine current library (arduinolib3) path")
    return None


def get_project_dir():
    """
    Get the project directory from PlatformIO environment or CMake environment.
    
    Returns:
        str: Path to the project directory, or None if not found
    """
    # Try PlatformIO environment first
    project_dir = None
    if env:
        project_dir = env.get("PROJECT_DIR", None)
    
    # If not found, try CMake environment variable
    if not project_dir:
        project_dir = os.environ.get("CMAKE_PROJECT_DIR", None)
    
    if project_dir:
        print(f"\nClient project directory: {project_dir}")
    else:
        print("Warning: Could not determine PROJECT_DIR from environment")
    return project_dir


# Get library scripts directory and add it to Python path
library_scripts_dir = get_library_dir()
sys.path.insert(0, str(library_scripts_dir))

# Set serializable macro name to _Entity
os.environ['SERIALIZABLE_MACRO'] = '_Entity'

# Get project directory
project_dir = get_project_dir()

# Get current library root directory (full path of arduinolib3 when included in client)
library_dir = get_current_library_path(project_dir)
if library_dir is None:
    # Fallback to parent of scripts directory
    library_dir = library_scripts_dir.parent
    print(f"Using fallback library directory: {library_dir}")
else:
    print(f"Current library (arduinolib3) path: {library_dir}")

# Print the library path with the requested message
print(f"Hello cuckoo, this is the library full path: {library_dir}")

# Import and execute scripts
from arduinolib3_execute_scripts import execute_scripts
execute_scripts(project_dir, library_dir)

print("arduinolib3 pre-build script completed successfully")

