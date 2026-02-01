"""
Nutrient SDK native libraries.

This package provides the native library files required by nutrient-sdk.
"""
import os
import sys
from pathlib import Path

__version__ = "1.0.0"


def _detect_platform_folder() -> str:
    """
    Detect the platform folder by scanning lib/ for available folders.

    Returns:
        str: The platform folder name (e.g., 'macos-universal', 'linux-amd64')

    Raises:
        RuntimeError: If no platform folder is found
    """
    lib_dir = Path(__file__).parent / "lib"
    if not lib_dir.exists():
        raise RuntimeError(f"lib directory not found: {lib_dir}")

    # Find the first subdirectory in lib/
    for item in lib_dir.iterdir():
        if item.is_dir():
            return item.name

    raise RuntimeError(f"No platform folder found in: {lib_dir}")


def _setup_environment() -> None:
    """
    Set up environment variables for native library loading.

    The native library is expected at:
    {NUTRIENT_NATIVE_SDK_PATH}/{platform}/NativeSDK.dylib|so|dll

    So we set NUTRIENT_NATIVE_SDK_PATH to the lib/ directory.
    """
    lib_dir = Path(__file__).parent / "lib"
    os.environ["NUTRIENT_NATIVE_SDK_PATH"] = str(lib_dir)


def get_library_path() -> str:
    """
    Get the path to the directory containing native libraries.

    Returns:
        str: Absolute path to the lib/{platform} directory
    """
    platform_folder = _detect_platform_folder()
    return str(Path(__file__).parent / "lib" / platform_folder)


def get_library_file() -> str:
    """
    Get the full path to the NativeSDK library file.

    Returns:
        str: Absolute path to libNativeSDK.dylib/so/dll

    Raises:
        FileNotFoundError: If the library file doesn't exist
    """
    # Set up environment before returning library path
    _setup_environment()

    platform_folder = _detect_platform_folder()
    lib_dir = Path(__file__).parent / "lib" / platform_folder

    # Try different library extensions
    for name in ["libNativeSDK.dylib", "libNativeSDK.so", "libNativeSDK.dll"]:
        lib_path = lib_dir / name
        if lib_path.exists():
            return str(lib_path)

    raise FileNotFoundError(f"Library not found in: {lib_dir}")


__all__ = ["get_library_path", "get_library_file", "__version__"]
