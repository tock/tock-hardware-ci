# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import logging

from gpio.interfaces.raspberry_pi5_gpio import RaspberryPi5GPIO
from gpio.interfaces.mock_gpio import MockGPIO


class GPIO:
    def __init__(self, target_spec):
        self.target_spec = target_spec
        self.gpio_interfaces = {}
        # Initialize GPIO interfaces based on the target spec
        for pin_label, pin_mapping in self.target_spec.get("pin_mappings", {}).items():
            interface_name = pin_mapping["io_interface"]
            if interface_name not in self.gpio_interfaces:
                interface_class = self.load_interface_class(interface_name)
                self.gpio_interfaces[interface_name] = interface_class()

    def load_interface_class(self, interface_name):
        # Map interface names to classes
        interface_classes = {
            "raspberrypi5gpio": RaspberryPi5GPIO,
            "mock_gpio": MockGPIO,
        }
        if interface_name in interface_classes:
            return interface_classes[interface_name]
        else:
            raise ValueError(f"Unknown GPIO interface: {interface_name}")

    def pin(self, pin_label):
        # Get the pin mapping from the target spec
        pin_mapping = self.target_spec["pin_mappings"].get(pin_label)
        if not pin_mapping:
            raise ValueError(f"Unknown pin label: {pin_label}")
        interface_name = pin_mapping["io_interface"]
        interface = self.gpio_interfaces.get(interface_name)
        if not interface:
            raise ValueError(f"No GPIO interface for {interface_name}")
        return interface.pin(pin_label, pin_mapping)
