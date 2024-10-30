# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

from core.board_harness import BoardHarness
import os
import subprocess
import logging
from contextlib import contextmanager


class TockloaderBoard(BoardHarness):

    def __init__(self):
        super().__init__()
        self.board = None  # Should be set in subclass
        self.arch = None  # Should be set in subclass
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    def flash_app(self, app_path):
        app_name = os.path.basename(app_path)
        logging.info(f"Flashing app: {app_name}")
        libtock_c_dir = os.path.join(self.base_dir, "libtock-c")
        if not os.path.exists(libtock_c_dir):
            logging.error(f"libtock-c directory {libtock_c_dir} not found")
            raise FileNotFoundError(f"libtock-c directory {libtock_c_dir} not found")

        app_dir = os.path.join(libtock_c_dir, "examples", app_path)
        if not os.path.exists(app_dir):
            logging.error(f"App directory {app_dir} not found")
            raise FileNotFoundError(f"App directory {app_dir} not found")

        # Build the app using absolute paths
        logging.info(f"Building app: {app_name}")
        subprocess.run(["make", f"TOCK_TARGETS={self.arch}"], cwd=app_dir, check=True)

        tab_file = os.path.join(app_dir, "build", f"{app_name}.tab")
        if not os.path.exists(tab_file):
            logging.error(f"Tab file {tab_file} not found")
            raise FileNotFoundError(f"Tab file {tab_file} not found")
        logging.info(f"Installing app: {app_name}")
        subprocess.run(
            [
                "tockloader",
                "install",
                "--board",
                self.board,
                "--openocd",
                tab_file,
            ],
            check=True,
        )

    def get_uart_port(self):
        pass

    def get_uart_baudrate(self):
        pass

    def erase_board(self):
        pass

    def flash_kernel(self):
        pass

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
