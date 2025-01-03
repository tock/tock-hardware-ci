# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
import re
from utils.test_helpers import OneshotTest

class SchedulerWhileoneBlinkTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["tests/whileone", "blink"])

    def oneshot_test(self, board):
        gpio = board.gpio
        serial = board.serial

        # Map the LEDs according to target_spec.yaml
        led_pins = {
            "LED1": gpio.pin("P0.13"),
            "LED2": gpio.pin("P0.14"),
        }

        # Configure LED pins as inputs to read their state
        for led in led_pins.values():
            led.set_mode("input")

        # Since the LEDs are active low, when the pin is low, the LED is on
        logging.info("Starting scheduler (whileone + blink) test")
        toggle_counts = {
            led: 0
            for led in led_pins.keys()
        }
        previous_states = {}
        for _ in range(50):  # Read the LED states multiple times
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

            time.sleep(0.1)  # Wait before next read

        # Make sure that each LED toggled at least twice, and the frequency of
        # toggles decreases with the LED index:
        prev_led = None
        prev_toggles = None
        for led, toggle_count in toggle_counts.items():
            assert toggle_count >= 2, f"LED {led} did not toggle at least 2 times!"
            assert prev_toggles is None or toggle_count < prev_toggles, \
                f"LED {led} toggled more ({toggle_count}) times than the previous LED ({prev_led}, {prev_toggles})"
            prev_toggles = toggle_count
            prev_led = led

        # Ensure that both apps are reported as running:
        serial.write(b"list\r\n")
        process_list_re = \
            r"PID[ \t]+ShortID[ \t]+Name[ \t]+Quanta[ \t]+Syscalls[ \t]+Restarts[ \t]+Grants[ \t]+State\r\n(.*)\r\n(.*)\r\n"
        process_list_out = serial.expect(process_list_re)
        assert process_list_out is not None
        process_list_match = re.match(process_list_re, process_list_out.decode("utf-8"))

        [whileone_proc, blink_proc] = \
            [process_list_match.group(1), process_list_match.group(2)] \
            if "whileone" in process_list_match.group(1) else \
            [process_list_match.group(2), process_list_match.group(1)]

        assert "whileone" in whileone_proc
        assert "Running" in whileone_proc
        assert "blink" in blink_proc
        assert "Running" in blink_proc or "Yielded" in blink_proc

        logging.info("Scheduler (whileone + blink) test completed successfully")

test = SchedulerWhileoneBlinkTest()
