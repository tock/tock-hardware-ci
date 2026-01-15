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

class LiteXArty(TockloaderBoard):
    def __init__(self):
        super().__init__()
        self.arch = "rv32imc"
        self.tock_targets = None
        self.kernel_path = os.path.join(
            self.base_dir, "repos/tock")
        self.kernel_board_path = os.path.join(
            self.kernel_path, "boards/litex/arty")
        self.uart_port = self.get_uart_port()
        self.uart_baudrate = self.get_uart_baudrate()
        self.board = "litex_arty"
        self.program_method = "none"
        self.program_args = ["--flash-file=/srv/tftp/boot.bin"]
        self.serial = self.get_serial_port()
        self.gpio = self.get_gpio_interface()
        self.open_serial_during_flash = True
        self.app_sha256_credential = False

    def get_uart_port(self):
        logging.info("Getting list of serial ports")
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if "Digilent USB Device" in port.description:
                logging.info(f"Found LiteX Arty UART: {port.device}")
                return port.device
        if ports:
            logging.info(f"Automatically selected port: {ports[0].device}")
            return ports[0].device
        else:
            logging.error("No serial ports found")
            raise Exception("No serial ports found")

    def get_uart_baudrate(self):
        return 1000000  # Default baudrate for the board

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

        # Run make program from the board directory
        subprocess.run(
            ["make"], cwd=self.kernel_board_path, check=True
        )
        # Then, flash this kernel into the board's flash file:
        subprocess.run(
            [
                "tockloader",
                "flash",
                "--board=litex_arty",
                "--flash-file=/srv/tftp/boot.bin",
                "--address=0x40000000",
                os.path.join(self.kernel_path, "target/riscv32imc-unknown-none-elf/release/litex_arty.bin"),
            ],
            cwd=self.kernel_board_path,
            check=True,
        )
        # Finally, reset the board:


    def erase_board(self):
        logging.info("Erasing the board")
        subprocess.run(
            [
                "truncate",
                "-s0",
                "/srv/tftp/boot.bin",
            ],
            check=True,
        )
        self.reset()

    def reset(self):
        if self.serial.is_open():
            self.serial.close()
            time.sleep(0.1)
            self.serial.open()
        else:
            self.serial.open()
            self.serial.close()

    def wait_boot(self):
        logging.info("Waiting 10sec for target to boot")
        time.sleep(15)

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


board = LiteXArty()
