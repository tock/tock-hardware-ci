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

        btn0 = gpio.pin("P0.11")
        btn0.set_mode("output")
        btn0.write(1)  # Ensure button is not pressed initially

        logging.info("Starting MPU Walk Region Test")

        # Wait for test start
        output = serial.expect(r"\[TEST\] MPU Walk Regions", timeout=10)
        if not output:
            raise Exception("Did not receive expected test start message")

        # First test: overrun flash region
        logging.info("First overrun test: Overrun flash region")
        output = serial.expect("Walking flash", timeout=5)
        if not output:
            raise Exception("Did not receive 'Walking flash' message")

        output = serial.expect("Walking memory", timeout=5)
        if not output:
            raise Exception("Did not receive 'Walking memory' message")

        output = serial.expect(" incr ", timeout=5)
        if not output:
            raise Exception("Did not receive 'incr' message")

        # Simulate button press
        btn0.write(0)
        logging.info("Button pressed (simulated)")

        # Wait for next walking flash message
        output = serial.expect("Walking flash", timeout=10)
        if not output:
            raise Exception(
                "Did not receive 'Walking flash' message after button press"
            )

        # Wait for fault
        output = serial.expect("mpu_walk_region had a fault", timeout=10)
        if not output:
            raise Exception("Did not receive MPU fault message")

        output = serial.expect(r"---\| Cortex-M Fault Status \|---", timeout=10)
        if not output:
            raise Exception("Did not receive Cortex-M fault status message")

        logging.info("First overrun test passed")

        # Release button and reset for second test
        btn0.write(1)
        logging.info("Button released (simulated)")

        logging.info("Resetting the board for the second test")
        board.erase_board()
        board.flash_kernel()
        board.flash_app("tests/mpu/mpu_walk_region")
        serial.flush_buffer()
        btn0.write(1)

        # Start second test
        output = serial.expect(r"\[TEST\] MPU Walk Regions", timeout=10)
        if not output:
            raise Exception(
                "Did not receive expected test start message for second test"
            )

        logging.info("Second overrun test: Overrun RAM region")
        output = serial.expect("Walking flash", timeout=10)
        if not output:
            raise Exception("Did not receive 'Walking flash' message in second test")

        output = serial.expect(" incr ", timeout=5)
        if not output:
            raise Exception("Did not receive 'incr' message during 'Walking flash'")

        btn0.write(0)
        logging.info("Button pressed (simulated)")

        output = serial.expect("Walking memory", timeout=5)
        if not output:
            raise Exception("Did not receive 'Walking memory' message in second test")

        # Wait for fault without requiring "Will overrun" message
        output = serial.expect("mpu_walk_region had a fault", timeout=10)
        if not output:
            raise Exception("Did not receive MPU fault message in second test")

        output = serial.expect(r"---\| Cortex-M Fault Status \|---", timeout=10)
        if not output:
            raise Exception(
                "Did not receive Cortex-M fault status message in second test"
            )

        logging.info("Second overrun test passed")
        logging.info("MPU Walk Region Test completed successfully")


test = MpuWalkRegionTest()
