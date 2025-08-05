#!/usr/bin/env python3
"""
Demo: Simplified hardware test that runs Rust-based tests in kernel.

This demonstrates how hardware tests could be much simpler - just flash
a test kernel and monitor the output, with all test logic in Rust.
"""

import logging
from utils.test_helpers import WaitForConsoleMessageTest


class RustHardwareTestDemo(WaitForConsoleMessageTest):
    """Demonstrates running hardware tests written in Rust."""
    
    # Use test kernel configuration
    KERNEL_CONFIG = "test"
    
    def __init__(self):
        # Monitor for the new hardware test output
        super().__init__(
            apps=[],  # No userspace apps needed!
            patterns=[
                # Traditional test output
                "Sha256Test: Verification result: Ok(true)",
                "hmac_test passed!",
                "siphash_test passed!",
                "aes_test passed (CTR Enc Ctr Src/Dst)",
                "aes_test passed (CBC Enc Src/Dst)",
                "aes_test passed (ECB Enc Src/Dst)",
                "ecdsa_p256_test passed!",
                
                # New hardware test framework output
                "Traditional tests finished. Running new hardware tests...",
                "=== Hardware Test Suite ===",
                "Running AES Hardware Test:",
                "Testing AES ECB mode...",
                "Testing AES in-place encryption...",
                "Testing AES performance...",
                "Overall: PASS",
                "=== Summary ===",
                "TEST SUITE: PASSED",
                "All tests finished."
            ],
            timeout=60
        )
    
    def test(self, board):
        """Override to set kernel config before running parent test."""
        # Configure board to use test kernel
        if hasattr(board, 'kernel_config'):
            board.kernel_config = self.KERNEL_CONFIG
            logging.info(f"Set kernel configuration to: {self.KERNEL_CONFIG}")
        
        # Run the parent test which handles flashing and monitoring
        super().test(board)
        
        logging.info("Hardware tests completed successfully!")


# For the test runner
test = RustHardwareTestDemo()