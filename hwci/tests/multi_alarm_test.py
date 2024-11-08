# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
from utils.test_helpers import OneshotTest


class MultiAlarmTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["tests/alarms/multi_alarm_test"])

    def oneshot_test(self, board):
        gpio = board.gpio

        led_pins = {}
        available_leds = ["LED1", "LED2", "LED3", "LED4"]  # Extend if needed
        for led_name in available_leds:
            try:
                led_pins[led_name] = gpio.pin(
                    f"P0.{13 + available_leds.index(led_name)}"
                )
            except ValueError:
                continue

        if not led_pins:
            raise Exception("No LEDs found in target_spec.yaml")

        for led in led_pins.values():
            led.set_mode("input")

        logging.info("Starting Multi-Alarm Test")

        num_leds = len(led_pins)
        spacing = 1.0  # seconds between each LED
        interval = spacing * num_leds  # Total interval in seconds
        test_duration = interval * 2 + spacing  # Ensure we capture at least two cycles

        start_time = time.time()

        # Record observed events
        observed_events = {led_name: [] for led_name in led_pins.keys()}
        led_states = {led_name: None for led_name in led_pins.keys()}

        end_time = start_time + test_duration  # Test duration in seconds

        first_event_time = None

        while time.time() < end_time:
            current_time = time.time()
            for led_name, pin in led_pins.items():
                value = pin.read()
                led_on = value == 0  # Active low
                if led_states[led_name] is None:
                    led_states[led_name] = led_on
                elif led_on != led_states[led_name]:
                    led_states[led_name] = led_on
                    event_time = current_time
                    logging.info(
                        f"{led_name} changed state to {'ON' if led_on else 'OFF'} at {event_time - start_time:.2f}s"
                    )
                    observed_events[led_name].append(
                        (event_time - start_time, "on" if led_on else "off")
                    )
                    if first_event_time is None:
                        first_event_time = (
                            event_time - start_time
                        )  # Record the time of the first event
            time.sleep(0.05)  # Sleep briefly to reduce CPU usage

        # If no events were observed, fail the test
        if all(len(events) == 0 for events in observed_events.values()):
            raise Exception("No LED events were observed during the test.")

        # Analyze the observed events
        for led_name, events in observed_events.items():
            if len(events) < 2:
                raise Exception(
                    f"{led_name}: Insufficient events observed ({len(events)} events)."
                )

            # Calculate the intervals between 'on' events
            on_times = [time for time, state in events if state == "on"]
            if len(on_times) < 2:
                raise Exception(f"{led_name}: Insufficient 'on' events observed.")

            intervals = [t2 - t1 for t1, t2 in zip(on_times, on_times[1:])]
            average_interval = sum(intervals) / len(intervals)
            expected_interval = interval

            # Allow for a tolerance in the interval calculation
            tolerance = 0.5  # seconds
            if abs(average_interval - expected_interval) > tolerance:
                raise Exception(
                    f"{led_name}: Interval between blinks is incorrect. Expected ~{expected_interval}s, observed ~{average_interval:.2f}s."
                )

            logging.info(
                f"{led_name}: Blinking at approximately {average_interval:.2f}s intervals."
            )

        logging.info("Multi-Alarm Test completed successfully")


test = MultiAlarmTest()
