# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import logging
import time
from core.test_harness import TestHarness


class RadioTxTest(TestHarness):
    """
    Test for IEEE 802.15.4 radio transmission functionality.

    This test flashes the 'radio_tx' application to a board and confirms
    that packets are being transmitted successfully.

    The test validates:
    1. The board can be programmed with the radio_tx app
    2. The radio transmits packets successfully (at least 95% success rate)
    3. Each packet transmission prints "Transmitted successfully" to the console
    """

    # Configuration constants
    TEST_DURATION = 10  # seconds
    EXPECTED_PACKETS = 40  # Packets expected in the test duration
    SUCCESS_THRESHOLD = 0.95  # 95% success rate required

    def test(self, boards):
        if len(boards) < 1:
            raise ValueError("Need at least 1 board for Radio TX test!")

        # Use the first board for the test
        board = boards[0]

        # Erase & reflash the kernel on the board
        logging.info(
            f"Preparing board for Radio TX test (SN: {getattr(board, 'serial_number', 'unknown')})"
        )
        board.erase_board()
        board.serial.flush_buffer()
        board.flash_kernel()

        # Flash the radio_tx app
        logging.info("Flashing radio_tx application")
        board.flash_app("tests/ieee802154/radio_tx")

        # Reset the board to start the test
        board.reset()

        # Collect output for TEST_DURATION seconds
        logging.info(f"Running test for {self.TEST_DURATION} seconds...")
        start_time = time.time()
        test_results = []

        while time.time() - start_time < self.TEST_DURATION:
            # Read any new line from the console
            line = board.serial.expect(".+\r?\n", timeout=1, timeout_error=False)
            if line:
                text = line.decode("utf-8", errors="replace").strip()
                logging.debug(f"[Radio TX] {text}")
                test_results.append(text)

        # Analyze test results
        success_count = 0
        for line in test_results:
            if "Transmitted successfully." in line:
                success_count += 1

        success_rate = success_count / self.EXPECTED_PACKETS
        logging.info(
            f"Packets transmitted successfully: {success_count}/{self.EXPECTED_PACKETS} ({success_rate:.2%})"
        )

        # Validate test results
        if success_rate >= self.SUCCESS_THRESHOLD:
            logging.info("PASSED: Radio TX test")
        else:
            error_message = f"FAILED: Radio TX test -- {success_count} out of {self.EXPECTED_PACKETS} packets transmitted successfully ({success_rate:.2%})"
            raise Exception(error_message)


# Global test object used by the HWCI framework
test = RadioTxTest()
