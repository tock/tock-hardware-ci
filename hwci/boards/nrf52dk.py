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
