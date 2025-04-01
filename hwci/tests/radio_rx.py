# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import logging
import time
from core.test_harness import TestHarness


class RadioRxTest(TestHarness):
    """
    Test for IEEE 802.15.4 radio reception functionality.

    This test requires two boards:
    - Board 0: Flashed with radio_tx app to transmit packets
    - Board 1: Flashed with radio_rx app to receive packets

    The test validates:
    1. Both boards can be programmed with their respective apps
    2. The receiver board detects the transmitted packets
    3. The received packets contain the expected data payload
    4. At least 80% of the expected packets are received correctly
    """

    # Configuration constants
    TEST_DURATION = 10  # seconds
    EXPECTED_PACKETS = 40  # Packets expected in the test duration
    SUCCESS_THRESHOLD = 0.80  # 80% success rate required

    def test(self, boards):
        if len(boards) < 2:
            raise ValueError("Need at least 2 boards for Radio RX test!")

        # Assign boards
        tx_board = boards[0]
        rx_board = boards[1]

        # Check that we're not using the same serial port for both boards
        if tx_board.uart_port == rx_board.uart_port:
            raise ValueError(
                f"Both boards are using the same serial port: {tx_board.uart_port}. "
                f"Each board must have a unique serial port. "
                f"TX Board SN: {getattr(tx_board, 'serial_number', 'unknown')}, "
                f"RX Board SN: {getattr(rx_board, 'serial_number', 'unknown')}"
            )

        # Prepare both boards
        logging.info(
            f"Preparing TX board (SN: {getattr(tx_board, 'serial_number', 'unknown')})"
        )
        tx_board.erase_board()
        tx_board.serial.flush_buffer()
        tx_board.flash_kernel()
        tx_board.flash_app("tests/ieee802154/radio_tx")

        logging.info(
            f"Preparing RX board (SN: {getattr(rx_board, 'serial_number', 'unknown')})"
        )
        rx_board.erase_board()
        rx_board.serial.flush_buffer()
        rx_board.flash_kernel()
        rx_board.flash_app("tests/ieee802154/radio_rx")

        # Reset both boards to start the test
        tx_board.reset()
        rx_board.reset()

        # Give the transmitter a moment to start up
        time.sleep(1)

        # Collect output from the receiver for TEST_DURATION seconds
        logging.info(f"Running test for {self.TEST_DURATION} seconds...")
        start_time = time.time()
        rx_results = []

        while time.time() - start_time < self.TEST_DURATION:
            # Read any new line from the RX console
            line = rx_board.serial.expect(".+\r?\n", timeout=1, timeout_error=False)
            if line:
                text = line.decode("utf-8", errors="replace").strip()
                logging.debug(f"[Radio RX] {text}")
                rx_results.append(text)

        # Analyze test results - look for complete packet reception patterns
        success_count = 0
        index = 0

        while index < len(rx_results):
            if (
                index + 8 < len(rx_results)
                and "Received packet with payload of 60 bytes from offset 12"
                in rx_results[index]
                and "00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f"
                in rx_results[index + 1]
                and "10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f"
                in rx_results[index + 2]
                and "20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f"
                in rx_results[index + 3]
                and "30 31 32 33 34 35 36 37 38 39 3a 3b" in rx_results[index + 4]
                and "Packet destination PAN ID: 0xabcd" in rx_results[index + 5]
                and "Packet destination address: 0x0802" in rx_results[index + 6]
                and "Packet source PAN ID: 0xabcd" in rx_results[index + 7]
                and "Packet source address: 0x1540" in rx_results[index + 8]
            ):
                success_count += 1
                index += 9
            else:
                index += 1

        success_rate = success_count / self.EXPECTED_PACKETS
        logging.info(
            f"Packets received successfully: {success_count}/{self.EXPECTED_PACKETS} ({success_rate:.2%})"
        )

        # Validate test results
        if success_rate >= self.SUCCESS_THRESHOLD:
            logging.info("PASSED: Radio RX test")
        else:
            error_message = f"FAILED: Radio RX test -- {success_count} out of {self.EXPECTED_PACKETS} packets received successfully ({success_rate:.2%})"
            raise Exception(error_message)


# Global test object used by the HWCI framework
test = RadioRxTest()
