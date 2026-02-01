"""Platform Detection Utilities.

This module provides utilities for detecting the current platform and architecture
for toolchain selection and package management.

Supported Platforms:
    - Windows: win32, win64
    - Linux: linux-amd64, linux-arm64, linux-armhf, linux-i686
    - macOS: macos, macos-arm64
"""

import platform
import sys
from typing import Literal, Tuple


class PlatformError(Exception):
    """Raised when platform detection fails or platform is unsupported."""

    pass


PlatformIdentifier = Literal[
    "win32",
    "win64",
    "linux-amd64",
    "linux-arm64",
    "linux-armhf",
    "linux-i686",
    "macos",
    "macos-arm64",
]


class PlatformDetector:
    """Detects the current platform and architecture for toolchain selection."""

    @staticmethod
    def detect_esp32_platform() -> str:
        """Detect the current platform for ESP32 toolchain selection.

        This format is used by ESP-IDF toolchain packages.

        Returns:
            Platform identifier (win32, win64, linux-amd64, linux-arm64, macos, macos-arm64)

        Raises:
            PlatformError: If platform is unsupported
        """
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "windows":
            # Check if 64-bit
            return "win64" if sys.maxsize > 2**32 else "win32"
        elif system == "linux":
            if "aarch64" in machine or "arm64" in machine:
                return "linux-arm64"
            elif "arm" in machine:
                # Check for hard float vs soft float
                return "linux-armhf"  # Default to hard float
            elif "i686" in machine or "i386" in machine:
                return "linux-i686"
            else:
                return "linux-amd64"
        elif system == "darwin":
            if "arm64" in machine or "aarch64" in machine:
                return "macos-arm64"
            else:
                return "macos"
        else:
            raise PlatformError(f"Unsupported platform: {system} {machine}")

    @staticmethod
    def detect_avr_platform() -> Tuple[str, str]:
        """Detect the current platform for AVR toolchain selection.

        This format is used by Arduino AVR toolchain packages.

        Returns:
            Tuple of (platform, architecture)
            Platform: 'windows', 'linux', or 'darwin'
            Architecture: 'x86_64', 'i686', 'aarch64', 'armv7l'

        Raises:
            PlatformError: If platform is not supported
        """
        system = platform.system().lower()
        machine = platform.machine().lower()

        # Normalize platform name
        if system == "windows":
            plat = "windows"
        elif system == "linux":
            plat = "linux"
        elif system == "darwin":
            plat = "darwin"
        else:
            raise PlatformError(f"Unsupported platform: {system}")

        # Normalize architecture
        if machine in ("x86_64", "amd64"):
            arch = "x86_64"
        elif machine in ("i386", "i686"):
            arch = "i686"
        elif machine in ("aarch64", "arm64"):
            arch = "aarch64"
        elif machine.startswith("arm"):
            arch = "armv7l"
        else:
            # Default to x86_64 if unknown
            arch = "x86_64"

        return plat, arch

    @staticmethod
    def get_platform_info() -> dict:
        """Get detailed information about the current platform.

        Returns:
            Dictionary with platform information including system, machine, and Python info
        """
        return {
            "system": platform.system(),
            "machine": platform.machine(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "is_64bit": sys.maxsize > 2**32,
            "esp32_format": PlatformDetector.detect_esp32_platform(),
            "avr_format": PlatformDetector.detect_avr_platform(),
        }
