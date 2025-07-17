# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2025.

"""
Test for IEEE 802.15.4 radio transmission functionality.
Tests that packets can be successfully transmitted using the radio.
"""

from hwci.utils.test_helpers import AnalyzeConsoleTest


class RadioTxTest(AnalyzeConsoleTest):
    def __init__(self):
        super().__init__(apps=["tests/ieee802154/radio_tx"])
        
    def analyze(self, output):
        # The TX test transmits a packet every 250ms. For a 10s test, we expect 40 packets
        # to be successfully transmitted. We check that 95% of packets do not fail.
        success_count = 0
        EXPECTED_PACKETS = 40  # Based on 10s runtime and 250ms interval
        
        for line in output:
            if "Transmitted successfully." in line:
                success_count += 1
        
        success_rate = success_count / EXPECTED_PACKETS if EXPECTED_PACKETS > 0 else 0
        
        # Check if 95% of packets were transmitted successfully
        assert success_rate >= 0.95, f"Radio TX test failed: only {success_count}/{EXPECTED_PACKETS} packets transmitted successfully ({success_rate:.1%})"
        
        print(f"Radio TX test passed: {success_count}/{EXPECTED_PACKETS} packets transmitted successfully")


test = RadioTxTest()