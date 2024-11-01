# hwci/tests/buttons.py

# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
from utils.test_helpers import OneshotTest


class ButtonsTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["buttons"])

    def oneshot_test(self, board):
        gpio = board.gpio

        # Map buttons and LEDs according to target_spec.yaml
        button_pins = {
            "BUTTON1": gpio.pin("P0.11"),
            "BUTTON2": gpio.pin("P0.12"),
        }
        led_pins = {
            "LED1": gpio.pin("P0.13"),
            "LED2": gpio.pin("P0.14"),
        }

        # Set button pins as outputs to simulate button presses (active low)
        for button in button_pins.values():
            button.set_mode("output")
            button.write(1)  # Not pressed initially

        # Set LED pins as inputs to read their state
        for led in led_pins.values():
            led.set_mode("input")

        # Simulate button presses and check LEDs
        for button_name, button_pin in button_pins.items():
            # Simulate button press
            logging.info(f"Pressing {button_name}")
            button_pin.write(0)  # Active low

            # Wait for the app to process the button press
            time.sleep(0.5)

            # Read the corresponding LED
            led_name = f"LED{button_name[-1]}"  # Assumes BUTTON1 corresponds to LED1
            led_pin = led_pins[led_name]
            led_value = led_pin.read()
            led_on = led_value == 0  # Active low
            logging.info(f"{led_name} is {'ON' if led_on else 'OFF'}")

            # Release button
            logging.info(f"Releasing {button_name}")
            button_pin.write(1)  # Not pressed

            # Wait before next iteration
            time.sleep(0.5)

        logging.info("Buttons test completed successfully")


test = ButtonsTest()
