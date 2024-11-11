# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.


class BoardHarness:
    arch = None
    kernel_board_path = None

    def __init__(self):
        self.serial = None
        self.gpio = None

    def get_uart_port(self):
        raise NotImplementedError

    def get_uart_baudrate(self):
        raise NotImplementedError

    def get_serial_port(self):
        raise NotImplementedError

    def get_gpio_interface(self):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError

    def erase_board(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def flash_kernel(self):
        raise NotImplementedError

    def flash_app(self, app):
        raise NotImplementedError
