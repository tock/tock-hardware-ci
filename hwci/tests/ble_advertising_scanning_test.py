# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

# python3 main.py \
#   --boards path/to/board1.py path/to/board2.py \
#   --apps ble_advertising ble_passive_scanning \
#   --test path/to/ble_advertising_scanning_test.py


import logging
import time
from core.test_harness import TestHarness


class MultiBoardTest(TestHarness):
    """
    This test expects two boards:
      - boards[0]: ble_advertising
      - boards[1]: ble_passive_scanning

    It checks that:
      (1) Board1 prints "Now advertising every ..."
      (2) Board2 subsequently prints "PDU Type:" which indicates it received an advertisement
    """

    def test(self, boards):
        if len(boards) < 2:
            raise Exception(
                "This test requires at least two boards: (1) ble_advertising, (2) ble_passive_scanning"
            )

        board1 = boards[0]  # Advertiser
        board2 = boards[1]  # Scanner

        logging.info("Starting BLE advertising and scanning test")

        # Flush buffers to ensure we start clean
        board1.serial.flush_buffer()
        board2.serial.flush_buffer()

        # Strings that indicate success on each board:
        advertiser_message_substr = "Now advertising every "
        scanner_message_substr = "PDU Type:"

        # We'll allow up to 30 seconds total for both conditions
        timeout = 30
        start_time = time.time()

        board1_advertising = False
        board2_detected_ad = False

        # We'll keep reading lines from each board in a loop with short timeouts
        while time.time() - start_time < timeout:
            # Check advertiser board if not already found
            if not board1_advertising:
                output = board1.serial.expect(r".*\r\n", timeout=1)
                if output:
                    decoded_line = output.decode("utf-8", errors="replace").strip()
                    logging.debug(f"Board1 output: {decoded_line}")
                    if advertiser_message_substr in decoded_line:
                        board1_advertising = True
                        logging.info("Board1: Confirmed advertising startup.")

            # Check scanner board if not already found
            if not board2_detected_ad:
                output = board2.serial.expect(r".*\r\n", timeout=1)
                if output:
                    decoded_line = output.decode("utf-8", errors="replace").strip()
                    logging.debug(f"Board2 output: {decoded_line}")
                    if scanner_message_substr in decoded_line:
                        board2_detected_ad = True
                        logging.info("Board2: Detected an incoming BLE advertisement.")

            # If both conditions are satisfied, we're done
            if board1_advertising and board2_detected_ad:
                logging.info(
                    "Both conditions met: Board1 is advertising and Board2 detected the advertisement."
                )
                break

        # Final check
        if not board1_advertising:
            raise Exception(
                "Timeout waiting for board1 to start advertising (didn't see 'Now advertising every ')"
            )
        if not board2_detected_ad:
            raise Exception(
                "Timeout waiting for board2 to detect an advertisement (didn't see 'PDU Type:')"
            )

        logging.info("BLE advertising and scanning test completed successfully")


# Instantiate the test class expected by your harness
test = MultiBoardTest()
