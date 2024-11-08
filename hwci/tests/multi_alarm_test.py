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

        # Map the LEDs according to target_spec.yaml
        led_pins = {
            "LED1": gpio.pin("P0.13"),
            "LED2": gpio.pin("P0.14"),
        }

        # Configure LED pins as inputs to read their state
        for led in led_pins.values():
            led.set_mode("input")

        # Since the LEDs are active low, when the pin is low, the LED is on
        logging.info("Starting Multi-Alarm Test")

        # Expected behavior:
        # Each LED starts blinking at specific times and repeats every interval

        # Get the number of LEDs
        num_leds = len(led_pins)
        spacing = 1.0  # seconds between each LED
        interval = spacing * num_leds  # Total interval in seconds

        start_time = time.time()

        # Initialize expected times for each LED
        expected_events = {}  # led_name: list of (expected_time, 'on'/'off')
        for idx, led_name in enumerate(led_pins.keys()):
            events = []
            # First event is 'on' at time spacing * (idx + 1)
            first_on_time = start_time + spacing * (idx + 1)
            time_point = first_on_time
            while time_point - start_time < 10:  # Test duration in seconds
                events.append((time_point, "on"))
                # LED stays on for 0.3 seconds
                off_time = time_point + 0.3
                if off_time - start_time < 10:
                    events.append((off_time, "off"))
                time_point += interval
            expected_events[led_name] = events

        # Record actual events
        observed_events = {led_name: [] for led_name in led_pins.keys()}
        led_states = {
            led_name: None for led_name in led_pins.keys()
        }  # Unknown initial state

        end_time = start_time + 10  # Test duration in seconds

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
                        (event_time, "on" if led_on else "off")
                    )
            time.sleep(0.05)  # Sleep briefly to reduce CPU usage

        # Compare observed events with expected events
        tolerance = 0.2  # Allow 200ms of tolerance
        for led_name in led_pins.keys():
            expected = expected_events[led_name]
            observed = observed_events[led_name]
            if len(expected) != len(observed):
                raise Exception(
                    f"{led_name}: Expected {len(expected)} events, observed {len(observed)} events"
                )
            for (exp_time, exp_state), (obs_time, obs_state) in zip(expected, observed):
                if exp_state != obs_state:
                    raise Exception(
                        f"{led_name}: Expected state '{exp_state}', observed '{obs_state}'"
                    )
                time_diff = abs(exp_time - obs_time)
                if time_diff > tolerance:
                    raise Exception(
                        f"{led_name}: Event at {obs_time - start_time:.2f}s differs from expected {exp_time - start_time:.2f}s by {time_diff:.2f}s"
                    )
        logging.info("Multi-Alarm Test completed successfully")


test = MultiAlarmTest()
