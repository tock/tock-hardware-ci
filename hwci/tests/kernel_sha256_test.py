# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

"""
Kernel test for SHA256 cryptographic functions.

This test runs the SHA256 implementation in the kernel without any userspace
involvement. It verifies that the SHA256 hash of "hello hello hello..." (72 bytes)
produces the correct hash value.
"""

from tests.kernel_test_base import KernelTestHarness
import logging

class Sha256KernelTest(KernelTestHarness):
    """Test the kernel's SHA256 implementation."""
    
    # Use the nrf52840dk-test-kernel configuration which includes crypto tests
    KERNEL_CONFIG = "test"
    
    def monitor_test_output(self, board):
        """Monitor serial output for SHA256 test results."""
        logging.info("Monitoring SHA256 kernel test output...")
        
        # The test kernel runs multiple tests in sequence.
        # First it will run the SHA256 test
        try:
            # Wait for SHA256 test to complete
            board.serial.expect("Sha256Test: Verification result: Ok\\(true\\)", timeout=30)
            logging.info("SHA256 test passed - hash verification succeeded!")
            
            # The test kernel continues with other tests (HMAC, SipHash, AES, etc.)
            # We can wait for all tests to complete
            board.serial.expect("All tests finished", timeout=120)
            logging.info("All kernel tests completed successfully!")
            
        except Exception as e:
            # Capture any error output
            error_output = board.serial.read()
            logging.error(f"SHA256 test failed: {e}")
            logging.error(f"Serial output: {error_output}")
            raise AssertionError(f"SHA256 kernel test failed: {e}")

# Create test instance
test = Sha256KernelTest()