# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2025.

"""
nRF52840DK board with Thread Tutorial configuration.
This board configuration uses the thread tutorial kernel which includes
the PHY driver needed for raw IEEE 802.15.4 transmission.
"""

import os
import subprocess
import logging
from boards.nrf52dk import Nrf52dk


class Nrf52dkThread(Nrf52dk):
    def __init__(self):
        super().__init__()
        
        # Override the kernel board path to use the thread tutorial configuration
        self.kernel_board_path = os.path.join(
            self.kernel_path, "boards", "tutorials", "nrf52840dk-thread-tutorial"
        )
        
        # The binary name is also different for the thread tutorial
        self.kernel_binary_name = "nrf52840dk-thread-tutorial.bin"
    
    def flash_kernel(self):
        """
        Flash the Thread Tutorial Tock OS kernel using tockloader.
        """
        logging.info("Flashing the Thread Tutorial Tock OS kernel")
        if not os.path.exists(self.kernel_path):
            raise FileNotFoundError(f"Tock directory {self.kernel_path} not found")

        # Make sure the kernel is built and ready
        subprocess.run(
            ["make"],
            cwd=self.kernel_board_path,
            check=True,
        )

        # Path to the kernel binary (different name for thread tutorial)
        kernel_bin = os.path.join(
            self.kernel_path, "target/thumbv7em-none-eabi/release", self.kernel_binary_name
        )

        # Get the serial number of this board
        serial_number = getattr(self, "serial_number", None)
        if not serial_number:
            logging.warning(
                "No serial number specified for board. Using first available board."
            )

        # Build the tockloader command with the correct order of arguments
        tockloader_cmd = ["tockloader", "flash"]

        # Order matters! These flags must come AFTER the 'flash' command
        if serial_number:
            tockloader_cmd.extend(["--openocd-serial-number", serial_number])

        # Add the rest of the arguments
        tockloader_cmd.extend(
            [
                "--openocd",
                "--openocd-board",
                "nordic_nrf52_dk.cfg",
                "--address",
                "0x00000",
                "--board",
                "nrf52dk",
                kernel_bin,
            ]
        )

        # Run the tockloader command
        logging.info(f"Running tockloader command: {' '.join(tockloader_cmd)}")
        subprocess.run(
            tockloader_cmd,
            check=True,
        )


# Factory function to create board instance
def create_board(**kwargs):
    board = Nrf52dkThread()
    # Set attributes from board descriptor
    for key, value in kwargs.items():
        setattr(board, key, value)
    # Re-initialize components that depend on descriptor attributes
    if hasattr(board, 'update_serial_port'):
        board.update_serial_port()
    # Re-initialize GPIO with pin_mappings if available
    if hasattr(board, 'pin_mappings'):
        board.gpio = board.get_gpio_interface()
    return board