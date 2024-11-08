# hwci/tests/button_print.py

# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import logging
import time
from utils.test_helpers import OneshotTest


class ButtonPressTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["tests/button_print"])

    def oneshot_test(self, board):
        gpio = board.gpio
        serial = board.serial

        button_pin = gpio.pin("P0.11")
        # Set the pin as output to simulate button press (active low)
        button_pin.set_mode("output")
        # button_pin.write(1)

        # Start the test
        logging.info("Starting Button Press Test")

        # Wait for initial message
        output = serial.expect(r"\[TEST\] Button Press", timeout=10)
        if not output:
            raise Exception("Did not receive expected test start message")

        # Longer delay before button press to ensure board is ready
        time.sleep(2.0)

        # Simulate button press
        button_pin.write(0)  # Active low, so writing 0 simulates press
        logging.info("Button pressed (simulated)")

        # Hold button press longer before release
        time.sleep(1.0)

        # Release button
        button_pin.write(1)
        logging.info("Button released (simulated)")

        # Wait longer for the expected output
        output = serial.expect(r"Button Press! Button: 0 Status: 0", timeout=10)
        if not output:
            raise Exception("Did not receive expected button press message")

        logging.info("Button press message received")

        logging.info("Button Press Test completed successfully")


test = ButtonPressTest()
