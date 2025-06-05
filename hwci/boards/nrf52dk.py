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

        # Default kernel configuration (can be overridden)
        self.kernel_config = "nrf52840dk-test-usb"
        
        # Path to the nrf52840dk board folder in Tock
        self.kernel_board_path = os.path.join(
            self.kernel_path, "boards", "configurations", "nrf52840dk", self.kernel_config
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
        print(ports)

        # First, check if we have a serial_number to match
        board_serial = getattr(self, "serial_number", None)
        if board_serial:
            logging.info(f"Looking for serial port with J-Link SN: {board_serial}")

            # Find ports that match our serial number
            matching_ports = []
            for port in ports:
                # Check if our serial number is in the port's serial_number or hwid
                if (
                    hasattr(port, "serial_number")
                    and board_serial == port.serial_number
                ):
                    matching_ports.append(port)
                elif hasattr(port, "hwid") and board_serial in port.hwid:
                    matching_ports.append(port)

            # Sort matching ports by device name to pick the lower-numbered one
            if matching_ports:
                matching_ports.sort(key=lambda p: p.device)
                selected_port = matching_ports[0].device
                logging.info(
                    f"Found matching J-Link port for SN {board_serial}: {selected_port}"
                )
                return selected_port

            logging.warning(f"No serial port found matching J-Link SN: {board_serial}")

        # If no serial number is provided or we couldn't find a match,
        # just return the first J-Link port for now (this will be replaced later)
        jlink_ports = [p for p in ports if "J-Link" in p.description]

        if jlink_ports:
            selected_port = jlink_ports[0].device
            logging.info(
                f"No serial number provided or match found. Using first J-Link port: {selected_port}"
            )
            return selected_port

        # If no J-Link ports were found at all
        if ports:
            logging.warning(
                f"No J-Link ports found. Using first available port: {ports[0].device}"
            )
            return ports[0].device

        logging.error("No serial ports found")
        raise Exception("No serial ports found")

    def update_serial_port(self):
        """Update the serial port based on the current serial_number attribute."""
        if hasattr(self, "serial_number") and self.serial_number:
            old_port = self.uart_port
            self.uart_port = self.get_uart_port()
            if old_port != self.uart_port:
                logging.info(f"Updated serial port from {old_port} to {self.uart_port}")
                # Close the old serial port if it exists
                if self.serial:
                    self.serial.close()
                # Create a new serial port object
                self.serial = self.get_serial_port()

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
    
    def set_kernel_config(self, config_name):
        """Set the kernel configuration to use (e.g., 'nrf52840dk-test-usb' or 'nrf52840dk-usb-bulk')."""
        self.kernel_config = config_name
        self.kernel_board_path = os.path.join(
            self.kernel_path, "boards", "configurations", "nrf52840dk", self.kernel_config
        )
        logging.info(f"Set kernel configuration to: {config_name}")

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

        # Path to the kernel binary (name matches the configuration)
        kernel_bin = os.path.join(
            self.kernel_path, f"target/thumbv7em-none-eabi/release/{self.kernel_config}.bin"
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

    def flash_app(self, app):
        if type(app) == str:
            app_path = app
            app_name = os.path.basename(app_path)
            tab_file = os.path.join("build", f"{app_name}.tab")
        else:
            app_path = app["path"]
            app_name = app["name"]
            tab_file = app["tab_file"]  # relative to "path"

        logging.info(f"Flashing app: {app_name}")
        libtock_c_dir = os.path.join(self.base_dir, "repos", "libtock-c")
        if not os.path.exists(libtock_c_dir):
            logging.error(f"libtock-c directory {libtock_c_dir} not found")
            raise FileNotFoundError(f"libtock-c directory {libtock_c_dir} not found")

        app_dir = os.path.join(libtock_c_dir, "examples", app_path)
        if not os.path.exists(app_dir):
            logging.error(f"App directory {app_dir} not found")
            raise FileNotFoundError(f"App directory {app_dir} not found")

        # Build the app using absolute paths
        logging.info(f"Building app: {app_name}")
        if app_name != "lua-hello":
            subprocess.run(
                ["make", f"TOCK_TARGETS={self.arch}"], cwd=app_dir, check=True
            )
        else:
            # if the app is lua-hello, we need to build the libtock-c submodule first
            with self.change_directory(libtock_c_dir):
                subprocess.run(
                    ["make", f"TOCK_TARGETS={self.arch}"], cwd=app_dir, check=True
                )

        tab_path = os.path.join(app_dir, tab_file)
        if not os.path.exists(tab_path):
            logging.error(f"Tab file {tab_path} not found")
            raise FileNotFoundError(f"Tab file {tab_path} not found")

        logging.info(f"Installing app: {app_name}")

        # Get the serial number of this board
        serial_number = getattr(self, "serial_number", None)

        # Build the tockloader command with the correct order of arguments
        tockloader_cmd = ["tockloader", "install"]

        # Add serial number if available
        if serial_number:
            tockloader_cmd.extend(["--openocd-serial-number", serial_number])

        # Add the rest of the arguments
        tockloader_cmd.extend(
            [
                "--openocd",
                "--openocd-board",
                "nordic_nrf52_dk.cfg",
                "--board",
                self.board,
                tab_path,
            ]
        )

        # Run the tockloader command
        logging.info(f"Running tockloader command: {' '.join(tockloader_cmd)}")
        subprocess.run(
            tockloader_cmd,
            check=True,
        )

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
