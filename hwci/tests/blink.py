# hwci/tests/blink.py

# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
from utils.test_helpers import OneshotTest


class BlinkTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["blink"])

    def oneshot_test(self, board):
        gpio = board.gpio

        # Map the LEDs
        led_pins = {
            "LED1": gpio.pin("P0.13"),
            "LED2": gpio.pin("P0.14"),
        }

        # Configure LED pins as inputs to read their state
        for led in led_pins.values():
            led.set_mode("input")

        # Since the LEDs are active low, when the pin is low, the LED is on
        logging.info("Starting blink test")
        previous_states = {}
        for _ in range(10):  # Read the LED states multiple times
            current_states = {}
            for name, pin in led_pins.items():
                value = pin.read()
                led_on = value == 0  # Active low
                current_states[name] = led_on
                logging.info(f"{name} is {'ON' if led_on else 'OFF'}")

            # Compare with previous states to check for changes
            if previous_states:
                for name in led_pins.keys():
                    if current_states[name] != previous_states[name]:
                        logging.info(
                            f"{name} changed state to {'ON' if current_states[name] else 'OFF'}"
                        )
            previous_states = current_states

            time.sleep(0.5)  # Wait before next read

        logging.info("Blink test completed successfully")


test = BlinkTest()
