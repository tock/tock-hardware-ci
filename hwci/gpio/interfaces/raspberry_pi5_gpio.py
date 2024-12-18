# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import logging
from gpiozero import LED, Button, DigitalOutputDevice, DigitalInputDevice


class RaspberryPi5GPIO:
    def __init__(self):
        self.pins = {}

    def pin(self, _target_pin_label, target_pin_mapping):
        gpio_pin_number = int(target_pin_mapping["io_pin_spec"])
        if gpio_pin_number not in self.pins:
            pin = RaspberryPiGPIOPin(gpio_pin_number)
            self.pins[gpio_pin_number] = pin
        else:
            pin = self.pins[gpio_pin_number]
        return pin

    def cleanup(self):
        for pin in self.pins.values():
            pin.close()
        self.pins.clear()


class RaspberryPiGPIOPin:
    def __init__(self, gpio_pin_number):
        self.gpio_pin_number = gpio_pin_number
        self.device = None  # Will be initialized based on mode
        self.mode = None

    def set_mode(self, mode):
        if mode == "input":
            if self.device:
                self.device.close()
            self.device = DigitalInputDevice(self.gpio_pin_number)
            self.mode = mode
        elif mode == "output":
            if self.device:
                self.device.close()
            self.device = DigitalOutputDevice(self.gpio_pin_number)
            self.mode = mode
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def read(self):
        if self.mode != "input":
            raise RuntimeError("Pin is not set to input mode")
        value = self.device.value
        logging.debug(f"Read value {value} from pin {self.gpio_pin_number}")
        return value

    def write(self, value):
        if self.mode != "output":
            raise RuntimeError("Pin is not set to output mode")
        self.device.value = value
        logging.debug(f"Wrote value {value} to pin {self.gpio_pin_number}")

    def close(self):
        if self.device:
            self.device.close()
            self.device = None
