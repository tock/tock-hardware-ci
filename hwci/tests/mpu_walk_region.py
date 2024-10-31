# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
from utils.test_helpers import OneshotTest
import time


class MpuWalkRegionTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["tests/mpu/mpu_walk_region"])

    def oneshot_test(self, board):
        gpio = board.gpio
        serial = board.serial

        # Assuming 'BTN0' is 'P0.11' as per target_spec.yaml
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
        output = serial.expect("Walking flash", timeout=5)
        if not output:
            raise Exception("Did not receive 'Walking flash' message")
        # Wait for "Walking memory"
        output = serial.expect("Walking memory", timeout=5)
        if not output:
            raise Exception("Did not receive 'Walking memory' message")
        # Wait for " incr "
        output = serial.expect(" incr ", timeout=5)
        if not output:
            raise Exception("Did not receive 'incr' message")
        # Simulate button press (active low)
        btn0.write(0)
        logging.info("Button pressed (simulated)")
        # Wait for "Walking flash...Will overrun"
        output = serial.expect(r"Walking flash.*Will overrun", timeout=10)
        if not output:
            raise Exception("Did not receive 'Walking flash...Will overrun' message")
        # Wait for "mpu_walk_region had a fault"
        output = serial.expect("mpu_walk_region had a fault", timeout=10)
        if not output:
            raise Exception("Did not receive 'mpu_walk_region had a fault' message")
        # Wait for Cortex-M fault status message
        output = serial.expect(r"---\| Cortex-M Fault Status \|---", timeout=10)
        if not output:
            raise Exception("Did not receive Cortex-M fault status message")
        logging.info("First overrun test passed")

        # Release the button
        btn0.write(1)
        logging.info("Button released (simulated)")

        # Reset the board and re-flash the app for the second test
        logging.info("Resetting the board for the second test")
        board.erase_board()
        board.flash_kernel()
        board.flash_app("tests/mpu/mpu_walk_region")
        serial.flush_buffer()
        btn0.write(1)  # Ensure button is not pressed initially (inactive state)

        # Start the test again
        output = serial.expect(r"\[TEST\] MPU Walk Regions", timeout=10)
        if not output:
            raise Exception(
                "Did not receive expected test start message for second test"
            )

        # Second test: overrun RAM region
        logging.info("Second overrun test: Overrun RAM region")
        # Wait for "Walking flash"
        output = serial.expect("Walking flash", timeout=10)
        if not output:
            raise Exception("Did not receive 'Walking flash' message in second test")
        # Wait for 'incr' message indicating 'Walking flash' is done
        output = serial.expect(" incr ", timeout=5)
        if not output:
            raise Exception("Did not receive 'incr' message during 'Walking flash'")
        # Simulate button press (active low) before walking memory
        btn0.write(0)
        logging.info("Button pressed (simulated)")
        # Wait for "Walking memory"
        output = serial.expect("Walking memory", timeout=5)
        if not output:
            raise Exception("Did not receive 'Walking memory' message in second test")
        # Wait for "Walking memory...Will overrun"
        output = serial.expect(r"Walking memory.*Will overrun", timeout=10)
        if not output:
            raise Exception("Did not receive 'Walking memory...Will overrun' message")
        # Wait for "mpu_walk_region had a fault"
        output = serial.expect("mpu_walk_region had a fault", timeout=10)
        if not output:
            raise Exception("Did not receive 'mpu_walk_region had a fault' message")
        # Wait for Cortex-M fault status message
        output = serial.expect(r"---\| Cortex-M Fault Status \|---", timeout=10)
        if not output:
            raise Exception(
                "Did not receive Cortex-M fault status message in second test"
            )
        logging.info("Second overrun test passed")

        logging.info("MPU Walk Region Test completed successfully")


test = MpuWalkRegionTest()
