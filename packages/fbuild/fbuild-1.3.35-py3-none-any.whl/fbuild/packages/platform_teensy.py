"""Teensy Platform Package Management.

This module coordinates Teensy platform components including toolchain and framework.
It provides a unified interface for managing Teensy 4.x platform builds.

Platform Components:
    - ARM GCC Toolchain (arm-none-eabi-gcc)
    - Teensy Cores Framework (Arduino core for Teensy 4.x)

Supported Boards:
    - Teensy 4.1 (NXP i.MX RT1062, ARM Cortex-M7 @ 600MHz)
    - Teensy 4.0 (NXP i.MX RT1062, ARM Cortex-M7 @ 600MHz)
"""

from pathlib import Path
from typing import Any, Dict, List

from .cache import Cache
from .framework_teensy import FrameworkErrorTeensy, FrameworkTeensy
from .package import IPackage, PackageError
from .toolchain_teensy import ToolchainErrorTeensy, ToolchainTeensy


class PlatformErrorTeensy(PackageError):
    """Raised when Teensy platform operations fail."""

    pass


class PlatformTeensy(IPackage):
    """Manages Teensy platform components and configuration.

    This class coordinates the Teensy toolchain and framework to provide
    a complete build environment for Teensy 4.x boards.
    """

    def __init__(self, cache: Cache, board_mcu: str, show_progress: bool = True):
        """Initialize Teensy platform manager.

        Args:
            cache: Cache manager instance
            board_mcu: MCU type (e.g., "imxrt1062")
            show_progress: Whether to show download/extraction progress
        """
        self.cache = cache
        self.board_mcu = board_mcu
        self.show_progress = show_progress

        # Initialize toolchain and framework
        self.toolchain = ToolchainTeensy(cache, show_progress=show_progress)
        self.framework = FrameworkTeensy(cache, show_progress=show_progress)

    def ensure_package(self) -> Path:
        """Ensure platform components are downloaded and extracted.

        Returns:
            Path to the framework directory (main platform directory)

        Raises:
            PlatformErrorTeensy: If download or extraction fails
        """
        try:
            # Ensure toolchain is installed
            self.toolchain.ensure_toolchain()

            # Ensure framework is installed
            framework_path = self.framework.ensure_framework()

            return framework_path

        except (ToolchainErrorTeensy, FrameworkErrorTeensy) as e:
            raise PlatformErrorTeensy(f"Failed to install Teensy platform: {e}")
        except KeyboardInterrupt as ke:
            from fbuild.interrupt_utils import handle_keyboard_interrupt_properly

            handle_keyboard_interrupt_properly(ke)
            raise  # Never reached, but satisfies type checker
        except Exception as e:
            raise PlatformErrorTeensy(f"Unexpected error installing platform: {e}")

    def is_installed(self) -> bool:
        """Check if platform is already installed.

        Returns:
            True if both toolchain and framework are installed
        """
        return self.toolchain.is_installed() and self.framework.is_installed()

    def get_compiler_flags(self, board_config: Any) -> List[str]:
        """Get compiler flags for Teensy builds.

        Args:
            board_config: Board configuration object

        Returns:
            List of compiler flags
        """
        flags = [
            # CPU and architecture
            "-mcpu=cortex-m7",
            "-mthumb",
            "-mfloat-abi=hard",
            "-mfpu=fpv5-d16",
            # Optimization
            "-O2",
            "-g",
            # Warnings
            "-Wall",
            "-Wextra",
            "-Wno-unused-parameter",
            # Standards
            "-std=gnu11",  # For C files
            # Board-specific defines
            f"-DF_CPU={board_config.f_cpu}",
            "-DARDUINO_TEENSY41",
            "-D__IMXRT1062__",
            "-DARDUINO=10819",
            "-DTEENSYDUINO=159",
            "-DUSB_SERIAL",
            # Memory layout
            "-DARDUINO_ARCH_TEENSY",
        ]

        return flags

    def get_compiler_flags_cpp(self, board_config: Any) -> List[str]:
        """Get C++ compiler flags for Teensy builds.

        Args:
            board_config: Board configuration object

        Returns:
            List of C++ compiler flags
        """
        # Start with base C flags
        flags = self.get_compiler_flags(board_config)

        # Replace C standard with C++ standard
        flags = [f for f in flags if not f.startswith("-std=gnu11")]
        flags.extend(
            [
                "-std=gnu++14",
                "-fno-exceptions",
                "-fno-rtti",
                "-felide-constructors",
                "-fno-threadsafe-statics",
            ]
        )

        return flags

    def get_linker_flags(self, board_config: Any, board_id: str = "teensy41") -> List[str]:
        """Get linker flags for Teensy builds.

        Args:
            board_config: Board configuration object
            board_id: Board identifier for linker script selection

        Returns:
            List of linker flags
        """
        # Get linker script
        linker_script = self.framework.get_linker_script(board_id)
        if not linker_script:
            raise PlatformErrorTeensy(f"Linker script not found for board: {board_id}")

        flags = [
            # CPU and architecture
            "-mcpu=cortex-m7",
            "-mthumb",
            "-mfloat-abi=hard",
            "-mfpu=fpv5-d16",
            # Optimization
            "-O2",
            # Linker script
            f"-T{linker_script}",
            # Linker options
            "-Wl,--gc-sections",
            "-Wl,--print-memory-usage",
            # Math library
            "-lm",
            "-lstdc++",
        ]

        return flags

    def get_include_dirs(self, board_config: Any) -> List[Path]:
        """Get include directories for Teensy builds.

        Args:
            board_config: Board configuration object

        Returns:
            List of include directory paths
        """
        includes = []

        # Core includes
        try:
            core_includes = self.framework.get_core_includes("teensy4")
            includes.extend(core_includes)
        except FrameworkErrorTeensy:
            pass

        return includes

    def get_core_sources(self) -> List[Path]:
        """Get core source files for Teensy builds.

        Returns:
            List of core source file paths
        """
        try:
            return self.framework.get_core_sources("teensy4")
        except FrameworkErrorTeensy:
            return []

    def get_toolchain_binaries(self) -> Dict[str, Path]:
        """Get paths to toolchain binaries.

        Returns:
            Dictionary mapping tool names to paths

        Raises:
            PlatformErrorTeensy: If toolchain binaries are not found
        """
        tools = self.toolchain.get_all_tool_paths()

        # Verify all required tools exist
        required_tools = ["gcc", "g++", "ar", "objcopy", "size"]
        for tool_name in required_tools:
            if tool_name not in tools or tools[tool_name] is None:
                raise PlatformErrorTeensy(f"Required tool not found: {tool_name}")

        # Filter out None values
        return {name: path for name, path in tools.items() if path is not None}

    def get_package_info(self) -> Dict[str, Any]:
        """Get information about the installed platform.

        Returns:
            Dictionary with platform information
        """
        return self.get_platform_info()

    def get_board_json(self, board_id: str) -> Dict[str, Any]:
        """Get board configuration in JSON format.

        This method returns board configuration compatible with the format
        expected by ConfigurableCompiler and ConfigurableLinker.

        Args:
            board_id: Board identifier (e.g., "teensy41")

        Returns:
            Dictionary containing board configuration

        Raises:
            PlatformErrorTeensy: If board is not supported
        """
        # Map board IDs to their configurations
        board_configs = {
            "teensy41": {
                "build": {
                    "mcu": "imxrt1062",
                    "f_cpu": "600000000L",
                    "core": "teensy4",
                    "variant": "teensy41",
                    "board": "TEENSY41",
                },
                "name": "Teensy 4.1",
                "upload": {
                    "maximum_size": 8126464,
                    "maximum_ram_size": 524288,
                },
            },
            "teensy40": {
                "build": {
                    "mcu": "imxrt1062",
                    "f_cpu": "600000000L",
                    "core": "teensy4",
                    "variant": "teensy40",
                    "board": "TEENSY40",
                },
                "name": "Teensy 4.0",
                "upload": {
                    "maximum_size": 2031616,
                    "maximum_ram_size": 524288,
                },
            },
        }

        if board_id not in board_configs:
            raise PlatformErrorTeensy(f"Unsupported board: {board_id}. " + f"Supported boards: {', '.join(board_configs.keys())}")

        return board_configs[board_id]

    def get_platform_info(self) -> Dict[str, Any]:
        """Get information about the installed platform.

        Returns:
            Dictionary with platform information
        """
        info = {
            "platform": "teensy",
            "mcu": self.board_mcu,
            "installed": self.is_installed(),
            "toolchain": self.toolchain.get_toolchain_info(),
            "framework": self.framework.get_framework_info(),
        }

        return info
