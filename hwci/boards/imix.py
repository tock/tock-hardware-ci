# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import time
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
import traceback

class Imix(TockloaderBoard):
    def __init__(self):
        super().__init__()
        self.arch = "cortex-m4"
        self.kernel_path = os.path.join(
            self.base_dir, "repos/tock")
        self.kernel_board_path = os.path.join(
            self.kernel_path, "boards/imix")
        self.uart_port = self.get_uart_port()
        self.uart_baudrate = self.get_uart_baudrate()
        self.board = "imix"
        self.program_method = "serial_bootloader"
        self.serial = self.get_serial_port()
        self.gpio = self.get_gpio_interface()
        self.open_serial_during_flash = False
        self.app_sha256_credential = True

    def get_uart_port(self):
        logging.info("Getting list of serial ports")
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if "imix IoT Module" in port.description:
                logging.info(f"Found imix IoT programming port: {port.device}")
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
        return SerialPort(self.uart_port, self.uart_baudrate, open_rts=False, open_dtr=True)

    def get_gpio_interface(self):
        return None

    def cleanup(self):
        if self.gpio:
            for interface in self.gpio.gpio_interfaces.values():
                interface.cleanup()
        if self.serial:
            self.serial.close()

    def flash_kernel(self):
        logging.info("Flashing the Tock OS kernel")
        if not os.path.exists(self.kernel_path):
            logging.error(f"Tock directory {self.kernel_path} not found")
            raise FileNotFoundError(f"Tock directory {self.kernel_path} not found")

        # Run make program from the board directory (this uses the Tock bootloader)
        subprocess.run(
            ["make", "program"], cwd=self.kernel_board_path, check=True
        )

    def erase_board(self):
        logging.info("Erasing the board")
        # We erase all apps, but don't erase the kernel. Is there a simple way
        # that we can prevent the installed kernel from starting (by
        # overwriting its reset vector?)
        subprocess.run(["tockloader", "erase-apps"], check=True)

    def reset(self):
        if self.serial.is_open():
            logging.info("Performing a target reset by toggling RTS")
            self.serial.set_rts(True)
            time.sleep(0.1)
            self.serial.set_rts(False)
        else:
            logging.info("Performing a target reset by reading address 0")
            subprocess.run(["tockloader", "read", "0x0", "1"], check=True)

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
    target_spec_path = os.path.join(os.getcwd(), "target_spec_imix.yaml")
    with open(target_spec_path, "r") as f:
        target_spec = yaml.safe_load(f)
    return target_spec


board = Imix()
