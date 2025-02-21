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
import yaml
import os


class Nrf52dk(TockloaderBoard):
    def __init__(self):
        super().__init__()
        self.arch = "cortex-m4"
        self.kernel_path = os.path.join(self.base_dir, "repos/tock")
        self.kernel_board_path = os.path.join(
            self.kernel_path, "boards/nordic/nrf52840dk"
        )
        self.uart_port = self.get_uart_port()
        self.uart_baudrate = self.get_uart_baudrate()
        self.openocd_board = "nrf52dk"
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
        return 115200  # Default baudrate for the board

    def get_serial_port(self):
        logging.info(
            f"Using serial port: {self.uart_port} at baudrate {self.uart_baudrate}"
        )
        return SerialPort(self.uart_port, self.uart_baudrate)

    def get_gpio_interface(self):
        # Instead of loading from target_spec.yaml, use self.pin_mappings
        if not hasattr(self, "pin_mappings"):
            logging.info(
                "No pin_mappings found in board descriptor; skipping GPIO init."
            )
            return None
        # The GPIO class expects a dict with a 'pin_mappings' key, so wrap it:
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
        Flash the Tock OS kernel onto this board using Tock's Makefile target.
        Pass the board's serial number via the JLINK_SERIAL env variable if known.
        """
        logging.info("Flashing the Tock OS kernel")
        if not os.path.exists(self.kernel_path):
            logging.error(f"Tock directory {self.kernel_path} not found")
            raise FileNotFoundError(f"Tock directory {self.kernel_path} not found")

        # Copy current environment and set JLINK_SERIAL if we have it:
        env = os.environ.copy()
        if getattr(self, "serial_number", None):
            env["JLINK_SERIAL"] = str(self.serial_number)
            logging.info(
                f"Setting JLINK_SERIAL={self.serial_number} for make flash-openocd"
            )

        # Run `make flash-openocd` from the board directory
        subprocess.run(
            ["make", "flash-openocd"],
            cwd=self.kernel_board_path,
            check=True,
            env=env,
        )

    def erase_board(self):
        """
        Run `nrf52_recover` to do a mass-erase and unlock the chip over SWD,
        specifying the adapter's serial if provided.
        """
        logging.info("Erasing the board")
        jlink_serial = getattr(self, "serial_number", None)

        if jlink_serial:
            # Use `adapter serial` rather than the deprecated `hla_serial`
            cmd_string = (
                f"adapter driver jlink; transport select swd; source [find target/nrf52.cfg]; "
                f"adapter serial {jlink_serial}; "
                "init; nrf52_recover; exit"
            )
        else:
            # If no serial number was given, fallback without specifying one
            cmd_string = (
                "adapter driver jlink; transport select swd; source [find target/nrf52.cfg]; "
                "init; nrf52_recover; exit"
            )

        command = ["openocd", "-c", cmd_string]
        logging.info(f"Running OpenOCD command: {command}")
        subprocess.run(command, check=True)

    def reset(self):
        """
        Issue a reset command over SWD.
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

    # The flash_app method is inherited from TockloaderBoard

    @contextmanager
    def change_directory(self, new_dir):
        previous_dir = os.getcwd()
        os.chdir(new_dir)
        logging.info(f"Changed directory to: {os.getcwd()}")
        try:
            yield
        finally:
            os.chdir(previous_dir)
            logging.info(f"Reverted to directory: {os.getcwd()}")


board = Nrf52dk()
