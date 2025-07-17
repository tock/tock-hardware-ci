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
        serial = board.serial
        
        # Wait for the application to initialize
        logging.info("Waiting for the application to initialize...")
        time.sleep(2)
        
        # Collect output for 10 seconds
        start_time = time.time()
        test_duration = 10  # seconds
        success_count = 0
        failure_count = 0
        
        logging.info(f"Collecting transmissions for {test_duration} seconds...")
        
        while time.time() - start_time < test_duration:
            try:
                # Use a more specific pattern to match transmission messages
                output = serial.expect(r'(Transmitted successfully\.|Transmit failed)', timeout=0.5, timeout_error=False)
                if output:
                    output_str = output.decode('utf-8', errors='replace') if isinstance(output, bytes) else str(output)
                    logging.debug(f"Matched output: {output_str}")
                    if "Transmitted successfully." in output_str:
                        success_count += 1
                    elif "Transmit failed" in output_str:
                        failure_count += 1
            except Exception as e:
                logging.debug(f"Exception during expect: {e}")
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
        
        # Check if we got any transmissions at all
        assert total_transmissions > 0, f"No transmissions detected! Check if the app is running correctly."
        
        # Check if we got a reasonable number of transmissions (at least 30 for a 10s test)
        assert total_transmissions >= 30, f"Too few transmissions detected: {total_transmissions} (expected ~40)"
        
        # Check if 95% of packets were transmitted successfully
        assert success_rate >= 0.95, f"Radio TX test failed: success rate {success_rate:.1%} is below 95%"
        
        print(f"Radio TX test passed: {success_count}/{total_transmissions} packets transmitted successfully ({success_rate:.1%})")


test = RadioTxTest()