"""
Debug utility module for pre-build scripts.
Provides a debug_print function that only prints when DEBUG flag is enabled.
"""

import os
import sys


# Check for debug flag from environment variable or command line arguments
def _is_debug_enabled():
    """
    Check if debug mode is enabled.
    
    Checks:
    1. Environment variable: PREBUILD_DEBUG or ARDUINOLIB_DEBUG
    2. Command line arguments: --debug, --verbose, -v, -d
    
    Returns:
        bool: True if debug mode is enabled, False otherwise
    """
    # Check environment variables
    if os.environ.get('PREBUILD_DEBUG', '').lower() in ('1', 'true', 'yes', 'on'):
        return True
    if os.environ.get('ARDUINOLIB_DEBUG', '').lower() in ('1', 'true', 'yes', 'on'):
        return True
    
    # Check command line arguments
    if '--debug' in sys.argv or '--verbose' in sys.argv or '-v' in sys.argv or '-d' in sys.argv:
        return True
    
    return False


# Cache the debug flag
_DEBUG_ENABLED = _is_debug_enabled()


def debug_print(*args, **kwargs):
    """
    Print message only if debug mode is enabled.
    
    Usage is identical to print(), but only outputs when debug flag is set.
    
    Args:
        *args: Arguments to pass to print()
        **kwargs: Keyword arguments to pass to print()
    """
    if _DEBUG_ENABLED:
        print(*args, **kwargs)


def debug_enabled():
    """
    Check if debug mode is currently enabled.
    
    Returns:
        bool: True if debug mode is enabled, False otherwise
    """
    return _DEBUG_ENABLED

