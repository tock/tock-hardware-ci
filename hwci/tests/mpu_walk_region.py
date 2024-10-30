# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
from utils.test_helpers import OneshotTest
import time


class MpuWalkRegionTest(OneshotTest):
    def oneshot_test(self, board):
        gpio = board.gpio
        serial = board.serial

        # Map 'BTN0' to the appropriate pin label in your target spec
        # Assuming 'BTN0' is 'P0.11' as per your target_spec.yaml
        btn0 = gpio.pin("P0.11")

        # Configure the pin as output to simulate button press (active low)
        btn0.set_mode("output")
        btn0.write(1)  # Ensure button is not pressed initially (inactive state)

        # Start the test
        logging.info("Starting MPU Walk Region Test")
        # Wait for "[TEST] MPU Walk Regions"
        output = serial.expect(r"\[TEST\] MPU Walk Regions", timeout=10)
        if not output:
            raise Exception("Did not receive expected test start message")

        # First test: overrun flash region
        logging.info("First overrun test: Overrun flash region")
        # Wait for "Walking flash"
        serial.expect("Walking flash", timeout=5)
        # Wait for "Walking memory"
        serial.expect("Walking memory", timeout=5)
        # Wait for " incr "
        serial.expect(" incr ", timeout=5)
        # Simulate button press (active low)
        btn0.write(0)
        logging.info("Button pressed (simulated)")
        # Wait for "Walking flash...Will overrun"
        serial.expect(r"Walking flash.*Will overrun", timeout=10)
        # Wait for "mpu_walk_region had a fault"
        serial.expect("mpu_walk_region had a fault", timeout=10)
        # Wait for "mcause: 0x00000005 (Load access fault)"
        serial.expect("mcause: 0x00000005 \(Load access fault\)", timeout=5)
        logging.info("First overrun test passed")

        # Release the button
        btn0.write(1)
        logging.info("Button released (simulated)")

        # Second test: overrun RAM region
        logging.info("Second overrun test: Overrun RAM region")
        # Wait for "Walking flash"
        serial.expect("Walking flash", timeout=10)
        # Wait for " incr "
        serial.expect(" incr ", timeout=5)
        # Simulate button press (active low)
        btn0.write(0)
        logging.info("Button pressed (simulated)")
        # Wait for "Walking memory...Will overrun"
        serial.expect(r"Walking memory.*Will overrun", timeout=10)
        # Wait for "mpu_walk_region had a fault"
        serial.expect("mpu_walk_region had a fault", timeout=10)
        # Wait for "mcause: 0x00000005 (Load access fault)"
        serial.expect("mcause: 0x00000005 \(Load access fault\)", timeout=5)
        logging.info("Second overrun test passed")

        logging.info("MPU Walk Region Test completed successfully")


test = MpuWalkRegionTest(["mpu_walk_region"])
