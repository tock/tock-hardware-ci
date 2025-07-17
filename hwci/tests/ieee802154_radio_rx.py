# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2025.

"""
Test for IEEE 802.15.4 radio receive functionality.
Tests packet transmission and reception between two boards.
"""

import time
from core.test_harness import TestHarness


class RadioRxTest(TestHarness):
    def __init__(self):
        super().__init__()
        
    def test(self, boards):
        # Require 2 boards for this test
        assert len(boards) >= 2, "Radio RX test requires at least 2 boards"
        
        board_tx = boards[0]
        board_rx = boards[1]
        
        # Erase and flash both boards
        board_tx.erase_board()
        board_tx.flash_kernel()
        board_tx.flash_app("tests/ieee802154/radio_tx")
        
        board_rx.erase_board()
        board_rx.flash_kernel()
        board_rx.flash_app("tests/ieee802154/radio_rx")
        
        # After flashing, boards automatically start running
        # Clear serial buffers
        board_tx.serial.flush_buffer()
        board_rx.serial.flush_buffer()
        
        # Give boards time to fully initialize after flashing
        time.sleep(2)
        
        # Collect output from RX board for 10 seconds
        start_time = time.time()
        rx_output = []
        
        while time.time() - start_time < 10:
            try:
                line = board_rx.serial.expect(r'.*', timeout=0.1)
                if line:
                    rx_output.append(line)
            except:
                continue
                
        # Analyze the received packets
        success_count = 0
        EXPECTED_PACKETS = 40  # Based on 250ms TX interval over 10s
        
        i = 0
        while i < len(rx_output):
            # Check for complete packet reception pattern
            if (i + 8 < len(rx_output) and
                "Received packet with payload of 60 bytes from offset 12" in rx_output[i] and
                "00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f" in rx_output[i+1] and
                "10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f" in rx_output[i+2] and
                "20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f" in rx_output[i+3] and
                "30 31 32 33 34 35 36 37 38 39 3a 3b" in rx_output[i+4] and
                "Packet destination PAN ID: 0xabcd" in rx_output[i+5] and
                "Packet destination address: 0x0802" in rx_output[i+6] and
                "Packet source PAN ID: 0xabcd" in rx_output[i+7] and
                "Packet source address: 0x1540" in rx_output[i+8]):
                success_count += 1
                i += 9
            else:
                i += 1
                
        success_rate = success_count / EXPECTED_PACKETS if EXPECTED_PACKETS > 0 else 0
        
        # Check if 80% of packets were received successfully (allowing for some loss)
        assert success_rate >= 0.80, f"Radio RX test failed: only {success_count}/{EXPECTED_PACKETS} packets received ({success_rate:.1%})"
        
        print(f"Radio RX test passed: {success_count}/{EXPECTED_PACKETS} packets received successfully")


test = RadioRxTest()