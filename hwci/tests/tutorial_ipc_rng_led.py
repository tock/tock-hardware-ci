# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
import re
from utils.test_helpers import OneshotTest


class TutorialIpcLedRngTest(OneshotTest):
    def __init__(self):
        super().__init__(
            apps=[
                {
                    "name": "led",
                    "path": "tutorials/05_ipc/led",
                    "tab_file": "build/org.tockos.tutorials.ipc.led.tab",
                },
                {
                    "name": "rng",
                    "path": "tutorials/05_ipc/rng",
                    "tab_file": "build/org.tockos.tutorials.ipc.rng.tab",
                },
                {
                    "name": "logic",
                    "path": "tutorials/05_ipc/logic",
                    "tab_file": "build/org.tockos.tutorials.ipc.logic.tab",
                },
            ]
        )

    def oneshot_test(self, board):
        gpio = board.gpio
        serial = board.serial

        # Map the LEDs according to the board_descriptor pin mappings
        led_pins = {
            "LED1": gpio.pin("P0.13"),
            "LED2": gpio.pin("P0.14"),
        }

        # Configure LED pins as inputs to read their state
        for led in led_pins.values():
            led.set_mode("input")

        # Since the LEDs are active low, when the pin is low, the LED is on
        logging.info("Starting IPC tutorial (LED + RNG) test")
        toggle_counts = {led: 0 for led in led_pins.keys()}
        previous_states = {}
        for _ in range(120):
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

            # If all LEDs have toggled at least once, the test passed:
            all_toggled = True
            for led, toggle_count in toggle_counts.items():
                if toggle_count == 0:
                    time.sleep(1)  # Wait before next read
                    all_toggled = False
                    break

            if all_toggled:
                # Test passed!
                logging.info("All LEDs toggled at least once, success!")
                return None

        raise AssertionError(f"Timed out waiting for all LEDs to toggle at least once!")


test = TutorialIpcLedRngTest()
