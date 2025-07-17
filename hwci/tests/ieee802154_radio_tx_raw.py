# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2025.

"""
Test for IEEE 802.15.4 raw radio transmission functionality.
Tests raw packet transmission between two boards.
"""

import time
import logging
from core.test_harness import TestHarness


class RadioTxRawTest(TestHarness):
    def __init__(self):
        super().__init__()
        
    def test(self, boards):
        # Require 2 boards for this test
        assert len(boards) >= 2, "Radio TX Raw test requires at least 2 boards"
        
        board_tx = boards[0]
        board_rx = boards[1]
        
        # Erase and flash both boards
        board_tx.erase_board()
        board_tx.flash_kernel()
        board_tx.flash_app("tests/ieee802154/radio_tx_raw")
        
        board_rx.erase_board()
        board_rx.flash_kernel()
        board_rx.flash_app("tests/ieee802154/radio_rx")
        
        # Wait for applications to initialize
        logging.info("Waiting for applications to initialize...")
        time.sleep(2)
        
        # Collect output from RX board for 10 seconds
        start_time = time.time()
        test_duration = 10
        rx_output = []
        
        logging.info(f"Collecting received packets for {test_duration} seconds...")
        
        while time.time() - start_time < test_duration:
            try:
                line = board_rx.serial.expect(r'.+', timeout=0.5, timeout_error=False)
                if line:
                    line_str = line.decode('utf-8', errors='replace') if isinstance(line, bytes) else str(line)
                    rx_output.append(line_str)
                    logging.debug(f"RX output: {line_str.strip()}")
            except Exception as e:
                logging.debug(f"Exception during expect: {e}")
                continue
                
        # Join all output into a single string to handle fragmented serial data
        full_output = ''.join(rx_output)
        
        # Count complete packet patterns in the joined output
        success_count = 0
        EXPECTED_PACKETS = 20  # Raw TX sends fewer packets
        
        # Use regex to find the pattern with flexible whitespace
        import re
        pattern_regex = re.compile(
            r"Received packet with payload of 60 bytes from offset 18\s+"
            r"00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f\s+"
            r"10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f\s+"
            r"20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f\s+"
            r"30 31 32 33 34 35 36 37 38 39 3a 3b\s+"
            r"Packet destination PAN ID: 0xabcd\s+"
            r"Packet destination address: 0xffff\s+"
            r"Packet source PAN ID: 0xabcd\s+"
            r"Packet source address: 00 00 00 00 00 00 00 00"
        )
        
        success_count = len(pattern_regex.findall(full_output))
                
        success_rate = success_count / EXPECTED_PACKETS if EXPECTED_PACKETS > 0 else 0
        
        # Check if 90% of packets were received successfully
        assert success_rate >= 0.90, f"Radio TX Raw test failed: only {success_count}/{EXPECTED_PACKETS} packets received ({success_rate:.1%})"
        
        print(f"Radio TX Raw test passed: {success_count}/{EXPECTED_PACKETS} packets received successfully")


test = RadioTxRawTest()