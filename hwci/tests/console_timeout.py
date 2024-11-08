# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
import re
from utils.test_helpers import OneshotTest


class ConsoleTimeoutTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["tests/console/console_timeout"])

    def oneshot_test(self, board):
        serial = board.serial

        # Wait for the application to initialize
        logging.info("Waiting for the application to initialize...")
        time.sleep(1)

        # Simulate user input by writing to the serial port
        test_input = b"Hello, Tock!"
        serial.write(test_input)
        logging.info(f"Sent test input: {test_input.decode('utf-8')}")

        # Wait for the expected output from the application
        logging.info("Waiting for the application to output the result...")
        output = serial.expect(
            r"Userspace call to read console returned: (.*)", timeout=10
        )
        if output:
            received_line = serial.child.after.decode("utf-8", errors="replace").strip()
            logging.info(f"Received output: {received_line}")
            match = re.search(
                r"Userspace call to read console returned: (.*)", received_line
            )
            if match:
                received_text = match.group(1)
                if received_text == test_input.decode("utf-8"):
                    logging.info("ConsoleTimeoutTest passed successfully.")
                else:
                    logging.error(
                        f"Expected '{test_input.decode('utf-8')}', but got '{received_text}'"
                    )
                    raise Exception("Test failed: Output does not match input.")
            else:
                raise Exception(
                    "Test failed: Could not parse the application's output."
                )
        else:
            raise Exception(
                "Test failed: Did not receive expected output from the application."
            )


test = ConsoleTimeoutTest()
