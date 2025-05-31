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
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.program_method = "serial_bootloader"
        self.app_sha256_credential = False

    def flash_app(self, app):
        if type(app) == str:
            app_path = app
            app_name = os.path.basename(app_path)
            tab_file = os.path.join("build", f"{app_name}.tab")
        else:
            app_path = app["path"]
            app_name = app["name"]
            tab_file = app["tab_file"] # relative to "path"

        logging.info(f"Flashing app: {app_name}")
        libtock_c_dir = os.path.join(self.base_dir, "repos", "libtock-c")
        if not os.path.exists(libtock_c_dir):
            logging.error(f"libtock-c directory {libtock_c_dir} not found")
            raise FileNotFoundError(f"libtock-c directory {libtock_c_dir} not found")

        app_dir = os.path.join(libtock_c_dir, "examples", app_path)
        if not os.path.exists(app_dir):
            logging.error(f"App directory {app_dir} not found")
            raise FileNotFoundError(f"App directory {app_dir} not found")


        make_args = [
            "make",
            f"TOCK_TARGETS={self.arch}"
        ]
        # if self.app_sha256_credential:
        #     make_args.append("ELF2TAB_ARGS=\"--sha256\"")

        # Build the app using absolute paths
        logging.info(f"Building app: {app_name}")
        if app_name != "lua-hello":
            subprocess.run(make_args, cwd=app_dir, check=True)
        else:
            # if the app is lua-hello, we need to build the libtock-c submodule first so we need to change directory
            # into the libtock-c directory so it knows we are in a git repostiory
            self.change_directory(libtock_c_dir)
            subprocess.run(make_args, cwd=app_dir, check=True)

        tab_path = os.path.join(app_dir, tab_file)
        if not os.path.exists(tab_path):
            logging.error(f"Tab file {tab_path} not found")
            raise FileNotFoundError(f"Tab file {tab_path} not found")

        if self.program_method == "serial_bootloader":
            program_method_arg = "--serial"
        elif self.program_method == "jlink":
            program_method_arg = "--jlink"
        elif self.program_method == "openocd":
            program_method_arg = "--openocd"
        else:
            raise NotImplemented(f"Unknown program method: {self.program_method}")

        logging.info(f"Installing app: {app_name}")
        subprocess.run(
            [
                "tockloader",
                "install",
                "--board",
                self.board,
                program_method_arg,
                tab_path,
            ],
            check=True,
        )

    def get_uart_port(self):
        raise NotImplementedError

    def get_uart_baudrate(self):
        raise NotImplementedError

    def erase_board(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def flash_kernel(self):
        raise NotImplementedError

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
