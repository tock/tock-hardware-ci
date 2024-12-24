# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
from utils.test_helpers import OneshotTest
import re


class StackSizeTest01(OneshotTest):
    def __init__(self):
        super().__init__(apps=[
            "tests/console/console_recv_short",
            "tests/console/console_recv_long",
        ])

    def oneshot_test(self, board):
        serial = board.serial
        return

        # Wait for "Stack Test App"
        output = serial.expect("Stack Test App", timeout=10)
        if not output:
            raise Exception("Did not receive 'Stack Test App' message")

        # Wait for "Current stack pointer: 0x..."
        output = serial.expect(r"Current stack pointer: 0x[0-9a-fA-F]+", timeout=5)
        if not output:
            raise Exception("Did not receive 'Current stack pointer' message")

        # Optionally, you can extract and log the stack pointer value
        match = re.search(r"Current stack pointer: (0x[0-9a-fA-F]+)", output.decode())
        if match:
            stack_pointer = match.group(1)
            logging.info(f"Stack pointer is at {stack_pointer}")
        else:
            raise Exception("Failed to parse stack pointer value")

        logging.info("Stack size test 01 completed successfully")


test = StackSizeTest01()
