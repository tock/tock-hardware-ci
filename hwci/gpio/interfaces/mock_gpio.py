# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import logging


class MockGPIO:
    def __init__(self):
        self.pins = {}

    def pin(self, target_pin_label, target_pin_mapping):
        if target_pin_label not in self.pins:
            pin = MockGPIOPin(target_pin_label)
            self.pins[target_pin_label] = pin
        else:
            pin = self.pins[target_pin_label]
        return pin

    def cleanup(self):
        pass  # Nothing to clean up in mock


class MockGPIOPin:
    def __init__(self, pin_label):
        self.pin_label = pin_label
        self.mode = None
        self.value = None

    def set_mode(self, mode):
        self.mode = mode
        logging.info(f"Pin {self.pin_label} set to mode {mode}")

    def read(self):
        logging.info(f"Pin {self.pin_label} read value {self.value}")
        return self.value

    def write(self, value):
        self.value = value
        logging.info(f"Pin {self.pin_label} write value {value}")
