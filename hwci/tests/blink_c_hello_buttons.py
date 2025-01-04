# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
import re
from utils.test_helpers import OneshotTest

class BlinkCHelloButtonsTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["blink", "c_hello", "buttons"])

    def oneshot_test(self, board):
        gpio = board.gpio
        serial = board.serial

        # Map the LEDs & buttons according to target_spec.yaml
        led_pins = {
            "LED1": gpio.pin("P0.13"),
            "LED2": gpio.pin("P0.14"),
        }
        button_pins = {
            "BUTTON1": gpio.pin("P0.11"),
            "BUTTON2": gpio.pin("P0.12"),
        }

        # Configure LED pins as inputs to read their state
        for led in led_pins.values():
            led.set_mode("input")

        # Configure Button pins as outputs
        for button in button_pins.values():
            button.set_mode("output")

        # Since the LEDs are active low, when the pin is low, the LED is on
        logging.info("Starting scheduler (whileone + blink) test")

        # First, ensure that we're seeing the Hello World message:
        assert serial.expect("Hello World!") is not None

        # Routine to record the amount of times that each LED was toggled,
        # while optionally toggling a button on each GPIO read:
        def count_led_toggles(toggle_button=None):
            toggle_counts = {
                led: 0
                for led in led_pins.keys()
            }
            previous_states = {}
            button_state = 0
            for _ in range(50):  # Read the LED states multiple times
                # Optionally toggle the button:
                if toggle_button is not None:
                    button_pins[toggle_button].write(button_state)
                    button_state = (button_state + 1) % 2

                # Read LED values:
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
                            toggle_counts[name] += 1
                previous_states = current_states

                time.sleep(0.05)  # Wait before next read

            return toggle_counts

        logging.info("Observing blink pattern without toggling buttons")
        base_toggle_counts = count_led_toggles()
        logging.info(f"LED toggle counts without toggling buttons: {base_toggle_counts}")

        for button_idx, button_label in enumerate(button_pins.keys()):
            logging.info(f"Observing blink pattern while toggling {button_label}")
            toggle_counts = count_led_toggles(toggle_button=button_label)
            logging.info(f"LED toggle counts while toggling button {button_label}: {toggle_counts}")

            # Ensure that for all LEDs where their corresponding button has not
            # been toggled, the observed blink frequency is roughly that of
            # the base toggle count above. For the LED where its button has
            # been toggled, its count should be significantly higher:
            for led_idx, (led_label, led_toggle_count) in enumerate(toggle_counts.items()):
                base_toggle_count = base_toggle_counts[led_label]
                if led_idx != button_idx:
                    assert led_toggle_count > base_toggle_count - 3 \
                        and led_toggle_count < base_toggle_count + 3, \
                        f"LED {led_label} toggle count {led_toggle_count} " \
                        + f"deviates from its base toggle count " \
                        + f"{base_toggle_count} by more than +-3 when " \
                        + f"pressing unrelated button {button_label}"
                else:
                    assert led_toggle_count > base_toggle_count + 3, \
                        f"LED {led_label} toggle count {led_toggle_count} " \
                        + f"is not significantly higher than its base toggle " \
                        + f"count {base_toggle_count} (+3) when toggling " \
                        + f"button {button_label}"

test = BlinkCHelloButtonsTest()
