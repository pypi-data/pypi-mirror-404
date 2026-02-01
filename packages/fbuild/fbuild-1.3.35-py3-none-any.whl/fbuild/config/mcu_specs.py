"""
MCU specifications for various embedded platforms.

This module centralizes hardware specifications like flash size and RAM
for different microcontrollers, making it easier to maintain and extend.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MCUSpec:
    """Hardware specifications for a microcontroller."""

    mcu_id: str
    max_flash: int  # Maximum flash size in bytes
    max_ram: int  # Maximum RAM size in bytes
    bootloader_size: int = 0  # Bootloader size in bytes (subtracted from flash)

    @property
    def usable_flash(self) -> int:
        """Get usable flash after accounting for bootloader."""
        return self.max_flash - self.bootloader_size


# AVR MCU specifications
AVR_SPECS = {
    "atmega328p": MCUSpec(
        mcu_id="atmega328p",
        max_flash=32768,  # 32KB
        max_ram=2048,  # 2KB
        bootloader_size=512,  # 512B bootloader
    ),
    "atmega2560": MCUSpec(
        mcu_id="atmega2560",
        max_flash=262144,  # 256KB
        max_ram=8192,  # 8KB
        bootloader_size=8192,  # 8KB bootloader
    ),
    "atmega32u4": MCUSpec(
        mcu_id="atmega32u4",
        max_flash=32768,  # 32KB
        max_ram=2560,  # 2.5KB
        bootloader_size=4096,  # 4KB bootloader
    ),
}


def get_mcu_spec(mcu_id: str) -> Optional[MCUSpec]:
    """
    Get MCU specifications by ID.

    Args:
        mcu_id: MCU identifier (e.g., 'atmega328p')

    Returns:
        MCUSpec if found, None otherwise
    """
    return AVR_SPECS.get(mcu_id.lower())


def get_max_flash(mcu_id: str) -> Optional[int]:
    """
    Get maximum usable flash for an MCU (after bootloader).

    Args:
        mcu_id: MCU identifier

    Returns:
        Usable flash size in bytes, or None if MCU not found
    """
    spec = get_mcu_spec(mcu_id)
    return spec.usable_flash if spec else None


def get_max_ram(mcu_id: str) -> Optional[int]:
    """
    Get maximum RAM for an MCU.

    Args:
        mcu_id: MCU identifier

    Returns:
        RAM size in bytes, or None if MCU not found
    """
    spec = get_mcu_spec(mcu_id)
    return spec.max_ram if spec else None
