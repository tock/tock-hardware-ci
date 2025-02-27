# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import os
import subprocess
import logging
from contextlib import contextmanager
import serial.tools.list_ports
from boards.tockloader_board import TockloaderBoard
from utils.serial_port import SerialPort
from gpio.gpio import GPIO


class Nrf52dk(TockloaderBoard):
    def __init__(self):
        super().__init__()
        self.arch = "cortex-m4"

        # Path to Tock's root directory
        self.kernel_path = os.path.join(self.base_dir, "repos", "tock")

        # Path to the nrf52840dk board folder in Tock
        self.kernel_board_path = os.path.join(
            self.kernel_path, "boards", "nordic", "nrf52840dk"
        )

        self.uart_port = self.get_uart_port()
        self.uart_baudrate = self.get_uart_baudrate()

        # Tockloader board info
        self.openocd_board = "nrf52dk"  # Matches `--board nrf52dk` in Tockloader
        self.board = "nrf52dk"

        self.serial = self.get_serial_port()
        self.gpio = self.get_gpio_interface()

    def get_uart_port(self):
        logging.info("Getting list of serial ports")
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if "J-Link" in port.description:
                logging.info(f"Found J-Link port: {port.device}")
                return port.device
        if ports:
            logging.info(f"Automatically selected port: {ports[0].device}")
            return ports[0].device
        else:
            logging.error("No serial ports found")
            raise Exception("No serial ports found")

    def get_uart_baudrate(self):
        return 115200

    def get_serial_port(self):
        logging.info(
            f"Using serial port: {self.uart_port} at baudrate {self.uart_baudrate}"
        )
        return SerialPort(self.uart_port, self.uart_baudrate)

    def get_gpio_interface(self):
        # If there is no 'pin_mappings' attribute, skip GPIO config
        if not hasattr(self, "pin_mappings"):
            logging.info(
                "No pin_mappings found in board descriptor; skipping GPIO init."
            )
            return None

        target_spec = {"pin_mappings": self.pin_mappings}
        return GPIO(target_spec)

    def cleanup(self):
        if self.gpio:
            for interface in self.gpio.gpio_interfaces.values():
                interface.cleanup()
        if self.serial:
            self.serial.close()

    def flash_kernel(self):
        """
        Flash the Tock OS kernel using tockloader directly with correct board config.
        """
        logging.info("Flashing the Tock OS kernel")
        if not os.path.exists(self.kernel_path):
            raise FileNotFoundError(f"Tock directory {self.kernel_path} not found")

        # Make sure the kernel is built and ready
        subprocess.run(
            ["make"],
            cwd=self.kernel_board_path,
            check=True,
        )

        # Path to the kernel binary
        kernel_bin = os.path.join(
            self.kernel_path, "target/thumbv7em-none-eabi/release/nrf52840dk.bin"
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
                "--debug",
                "--openocd-board",
                "board/nordic_nrf52_dk.cfg",  # Correct path we found
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

    def erase_board(self):
        """
        Issue an nrf52_recover over SWD, specifying 'adapter serial <SN>' if available.
        This uses OpenOCD directly to mass erase/unlock the chip.
        """
        logging.info("Erasing the board")
        jlink_serial = getattr(self, "serial_number", None)

        if jlink_serial:
            cmd_string = (
                f"adapter driver jlink; transport select swd; source [find target/nrf52.cfg]; "
                f"adapter serial {jlink_serial}; "
                "init; nrf52_recover; exit"
            )
        else:
            cmd_string = (
                "adapter driver jlink; transport select swd; source [find target/nrf52.cfg]; "
                "init; nrf52_recover; exit"
            )

        command = ["openocd", "-c", cmd_string]
        logging.info(f"Running OpenOCD command: {command}")
        subprocess.run(command, check=True)

    def reset(self):
        """
        Hard reset the board using OpenOCD, specifying the J-Link serial if we have one.
        """
        logging.info("Performing a target reset via JTAG/SWD")
        jlink_serial = getattr(self, "serial_number", None)

        if jlink_serial:
            cmd_string = (
                f"adapter driver jlink; transport select swd; source [find target/nrf52.cfg]; "
                f"adapter serial {jlink_serial}; "
                "init; reset; exit"
            )
        else:
            cmd_string = (
                "adapter driver jlink; transport select swd; source [find target/nrf52.cfg]; "
                "init; reset; exit"
            )

        command = ["openocd", "-c", cmd_string]
        logging.info(f"Running OpenOCD command: {command}")
        subprocess.run(command, check=True)

    @contextmanager
    def change_directory(self, new_dir):
        old_dir = os.getcwd()
        os.chdir(new_dir)
        logging.info(f"Changed directory to: {os.getcwd()}")
        try:
            yield
        finally:
            os.chdir(old_dir)
            logging.info(f"Reverted to directory: {os.getcwd()}")


# Global board object used by the test harness
board = Nrf52dk()
