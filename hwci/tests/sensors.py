# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
from utils.test_helpers import OneshotTest

class SensorsTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["sensors"])

    def oneshot_test(self, board):
        logging.info("Starting Sensors Test")
        serial = board.serial

        # Expected messages from the sensors app
        expected_messages = [
            r"\[Sensors\] Starting Sensors App.",
            r"\[Sensors\] All available sensors on the platform will be sampled.",
        ]

        # Read initial messages
        for message in expected_messages:
            output = serial.expect(message, timeout=10)
            if not output:
                raise Exception(f"Did not receive expected message: '{message}'")
            logging.info(f"Received expected message: '{message}'")

        # Now read sensor data outputs for a certain number of iterations
        iterations = 5  # Number of sensor readings to check
        for i in range(iterations):
            # Read sensor data output lines until the next blank line
            while True:
                output = serial.expect(r".*\r\n", timeout=5)
                if output:
                    line = output.decode("utf-8", errors="replace").strip()
                    if line == "":
                        # Blank line indicates the end of one sensor reading cycle
                        logging.info(f"Completed reading sensor data for iteration {i+1}")
                        break
                    else:
                        logging.info(f"Sensor output: {line}")
                else:
                    raise Exception("Timeout while reading sensor data")

        logging.info("Sensors Test completed successfully")

test = SensorsTest()    
