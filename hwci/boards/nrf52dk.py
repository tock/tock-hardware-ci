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


class Nrf52dk(TockloaderBoard):
    def __init__(self, serial_number=None, exclude_serial=None):
        super().__init__()
        self.arch = "cortex-m4"
        self.serial_number = serial_number
        self.exclude_serial = exclude_serial
        self.kernel_board_path = os.path.join(
            self.base_dir, "tock/boards/nordic/nrf52840dk"
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

        # Filter for J-Link devices
        jlink_ports = [port for port in ports if "J-Link" in port.description]

        if not jlink_ports:
            logging.error("No J-Link devices found")
            raise Exception("No J-Link devices found")

        # Log available boards
        for port in jlink_ports:
            logging.info(
                f"Found J-Link device: {port.device} (Serial: {port.serial_number})"
            )

        selected_port = None

        # If we're looking for a specific serial number
        if self.serial_number:
            for port in jlink_ports:
                if port.serial_number == self.serial_number:
                    selected_port = port
                    break
            if not selected_port:
                raise Exception(
                    f"No J-Link device found with serial number {self.serial_number}"
                )

        # If we're excluding a specific serial number
        elif self.exclude_serial:
            for port in jlink_ports:
                if port.serial_number != self.exclude_serial:
                    selected_port = port
                    break
            if not selected_port:
                raise Exception(
                    f"No J-Link device found other than {self.exclude_serial}"
                )

        # If no specific selection criteria, use the first available port
        else:
            selected_port = jlink_ports[0]

        logging.info(
            f"Selected J-Link device: {selected_port.device} (Serial: {selected_port.serial_number})"
        )
        return selected_port.device

    def get_board_serial(board):
        """Get the serial number of the J-Link device associated with the board."""
        port = next(
            port
            for port in serial.tools.list_ports.comports()
            if port.device == board.uart_port
        )

        return port.serial_number

    def get_uart_baudrate(self):
        return 115200  # Default baudrate for the board

    def get_serial_port(self):
        logging.info(
            f"Using serial port: {self.uart_port} at baudrate {self.uart_baudrate}"
        )
        return SerialPort(self.uart_port, self.uart_baudrate)

    def get_gpio_interface(self):
        # Load the target spec from a YAML file
        target_spec = load_target_spec()
        # Initialize GPIO with the target spec
        gpio = GPIO(target_spec)
        return gpio

    def cleanup(self):
        if self.gpio:
            for interface in self.gpio.gpio_interfaces.values():
                interface.cleanup()
        if self.serial:
            self.serial.close()

    def flash_kernel(self):
        logging.info("Flashing the Tock OS kernel")
        tock_dir = os.path.join(self.base_dir, "tock")
        if not os.path.exists(tock_dir):
            logging.error(f"Tock directory {tock_dir} not found")
            raise FileNotFoundError(f"Tock directory {tock_dir} not found")

        # Run make flash-openocd from the board directory
        subprocess.run(
            ["make", "flash-openocd"], cwd=self.kernel_board_path, check=True
        )

    def erase_board(self):
        logging.info("Erasing the board")
        command = [
            "openocd",
            "-c",
            "adapter driver jlink; transport select swd; source [find target/nrf52.cfg]; init; nrf52_recover; exit",
        ]
        subprocess.run(command, check=True)

    def reset(self):
        logging.info("Performing a target reset via JTAG")
        command = [
            "openocd",
            "-c",
            "adapter driver jlink; transport select swd; source [find target/nrf52.cfg]; init; reset; exit",
        ]
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


def load_target_spec():
    # Assume the target spec file is in a fixed location
    target_spec_path = os.path.join(os.getcwd(), "target_spec.yaml")
    with open(target_spec_path, "r") as f:
        target_spec = yaml.safe_load(f)
    return target_spec


board = Nrf52dk()
