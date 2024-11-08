# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
from utils.test_helpers import OneshotTest


class GpioOriginalTest(OneshotTest):
    def __init__(self):
        # Specify the path to the app relative to the libtock-c examples directory
        super().__init__(apps=["tests/gpio/gpio_original"])

    def oneshot_test(self, board):
        gpio = board.gpio

        gpio_pin_label = "P0.13"
        try:
            gpio_pin = gpio.pin(gpio_pin_label)
        except ValueError as e:
            logging.error(f"GPIO pin {gpio_pin_label} not found in target_spec.yaml")
            raise e

        # Configure GPIO pin as input to read its state
        gpio_pin.set_mode("input")

        logging.info("Starting GPIO original test (gpio_output mode)")

        previous_state = None
        start_time = time.time()

        test_duration = 10  # seconds
        end_time = start_time + test_duration

        last_toggle_time = None
        toggle_intervals = []

        while time.time() < end_time:
            value = gpio_pin.read()
            # GPIO is active high in this context
            gpio_on = value == 1
            logging.debug(f"GPIO pin value: {value}")

            if previous_state is not None and gpio_on != previous_state:
                current_time = time.time()
                elapsed_time = current_time - start_time
                logging.info(
                    f"GPIO pin toggled to {gpio_on} at {elapsed_time:.2f} seconds"
                )
                if last_toggle_time is not None:
                    interval = current_time - last_toggle_time
                    toggle_intervals.append(interval)
                    logging.info(f"Time since last toggle: {interval:.2f} seconds")
                last_toggle_time = current_time
            previous_state = gpio_on

            time.sleep(0.1)  # Sample every 0.1 seconds

        # Analyze toggle intervals
        if len(toggle_intervals) == 0:
            raise Exception("No toggles detected on GPIO pin during test duration")
        else:
            average_interval = sum(toggle_intervals) / len(toggle_intervals)
            expected_interval = 1.0  # seconds, as per app's behavior
            tolerance = 0.5  # seconds
            if abs(average_interval - expected_interval) > tolerance:
                raise Exception(
                    f"GPIO pin toggled at incorrect intervals. Expected ~{expected_interval}s, observed ~{average_interval:.2f}s."
                )
            else:
                logging.info(
                    f"GPIO pin toggled at approximately {average_interval:.2f}s intervals."
                )
                logging.info("GPIO original test completed successfully")


test = GpioOriginalTest()
