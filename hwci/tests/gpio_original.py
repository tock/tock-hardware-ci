# hwci/tests/gpio_test.py

# Licensed under the Apache License, Version 2.0 or MIT
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
from utils.test_helpers import OneshotTest
import time


class GpioTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["tests/gpio/gpio_original"])

    def oneshot_test(self, board):
        gpio = board.gpio

        gpio_pin = gpio.pin("P0.11")
        gpio_pin.set_mode("output")

        logging.info("Starting GPIO test")
        time.sleep(1)  # Allow app to start

        for _ in range(5):
            value = gpio_pin.read()
            logging.info(f"GPIO value: {value}")
            time.sleep(1)

        logging.info("GPIO test completed")


test = GpioTest()
