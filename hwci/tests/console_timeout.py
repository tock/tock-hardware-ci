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
        time.sleep(2)  # Allow time for the app to start

        # Simulate user input by writing to the serial port
        test_input = b"Hello, Tock!"
        serial.write(test_input)
        logging.info(f"Sent test input: {test_input.decode('utf-8')}")
        time.sleep(7)  # Wait for the application to process

        # Wait for the expected output from the application
        logging.info("Waiting for the application to output the result...")
        pattern = r"Userspace call to read console returned: (.*)"
        output = serial.expect(pattern, timeout=10)

        if output:
            received_line = output.decode("utf-8", errors="replace").strip()
            logging.info(f"Received output: {received_line}")
            match = serial.child.match  # Use the match object from serial.expect
            if match:
                received_text = match.group(1).decode(
                    "utf-8", errors="replace"
                )  # Decode bytes to str
                expected_text = test_input.decode("utf-8")
                if received_text.strip() == expected_text.strip():
                    logging.info("ConsoleTimeoutTest passed successfully.")
                else:
                    logging.error(
                        f"Expected text '{expected_text}', but got '{received_text}'"
                    )
                    raise Exception(
                        "Test failed: Output does not match expected input."
                    )
            else:
                raise Exception(
                    "Test failed: Could not parse the application's output."
                )
        else:
            raise Exception(
                "Test failed: Did not receive expected output from the application."
            )


test = ConsoleTimeoutTest()
