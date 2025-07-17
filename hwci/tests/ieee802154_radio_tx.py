# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2025.

"""
Test for IEEE 802.15.4 radio transmission functionality.
Tests that packets can be successfully transmitted using the radio.
"""

import time
import logging
from utils.test_helpers import OneshotTest


class RadioTxTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["tests/ieee802154/radio_tx"])
        
    def oneshot_test(self, board):
        logging.info("Starting Radio TX test")
        
        # Collect output for 10 seconds
        start_time = time.time()
        test_duration = 10  # seconds
        success_count = 0
        failure_count = 0
        
        while time.time() - start_time < test_duration:
            try:
                line = board.serial.expect(r'.*', timeout=0.5)
                if line:
                    line_str = line.decode('utf-8', errors='replace') if isinstance(line, bytes) else str(line)
                    if "Transmitted successfully." in line_str:
                        success_count += 1
                    elif "Transmit failed" in line_str:
                        failure_count += 1
            except:
                continue
        
        # The TX test transmits a packet every 250ms. For a 10s test, we expect ~40 packets
        # Allow some variation due to startup time
        total_transmissions = success_count + failure_count
        success_rate = success_count / total_transmissions if total_transmissions > 0 else 0
        
        logging.info(f"Test ran for {test_duration} seconds")
        logging.info(f"Successful transmissions: {success_count}")
        logging.info(f"Failed transmissions: {failure_count}")
        logging.info(f"Total transmissions: {total_transmissions}")
        logging.info(f"Success rate: {success_rate:.1%}")
        
        # Check if 95% of packets were transmitted successfully
        assert total_transmissions >= 30, f"Too few transmissions detected: {total_transmissions} (expected ~40)"
        assert success_rate >= 0.95, f"Radio TX test failed: success rate {success_rate:.1%} is below 95%"
        
        print(f"Radio TX test passed: {success_count}/{total_transmissions} packets transmitted successfully ({success_rate:.1%})")


test = RadioTxTest()