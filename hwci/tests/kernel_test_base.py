# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

"""Base class for kernel-only tests that don't require userspace."""

from core.test_harness import TestHarness
import logging
import re

class KernelTestHarness(TestHarness):
    """
    Base class for kernel-only tests.
    
    These tests use special kernel configurations that include test modules
    and run without any userspace processes (NUM_PROCS = 0).
    """
    
    # Override in subclasses to specify the kernel configuration
    KERNEL_CONFIG = "test"
    
    # Timeout for the entire test run (in seconds)
    TEST_TIMEOUT = 60
    
    def test(self, boards):
        """Run the kernel test on the specified board."""
        if len(boards) != 1:
            raise ValueError("Kernel tests require exactly one board")
            
        board = boards[0]
        
        # Configure board for test kernel
        if hasattr(board, 'kernel_config'):
            board.kernel_config = self.KERNEL_CONFIG
            logging.info(f"Set kernel configuration to: {self.KERNEL_CONFIG}")
        else:
            raise AttributeError(f"Board {board} does not support kernel_config")
        
        # Flash the test kernel
        logging.info("Erasing board...")
        board.erase_board()
        
        logging.info(f"Flashing {self.KERNEL_CONFIG} kernel...")
        board.flash_kernel()
        
        # Reset board to start test execution
        logging.info("Resetting board to start tests...")
        board.reset()
        
        # Monitor test output
        self.monitor_test_output(board)
    
    def monitor_test_output(self, board):
        """
        Monitor serial output for test results.
        Override in subclasses to check specific test outputs.
        """
        raise NotImplementedError("Subclasses must implement monitor_test_output")
    
    def expect_test_pass(self, board, test_name, timeout=30):
        """Helper to wait for a test pass message."""
        patterns = [
            f"{test_name}.*[Pp]assed",
            f"{test_name}.*[Ss]uccess",
            f"{test_name}.*[Oo][Kk]",
            f"{test_name}.*Verification result: Ok\\(true\\)"
        ]
        
        for pattern in patterns:
            try:
                board.serial.expect(pattern, timeout=timeout)
                logging.info(f"Test {test_name} passed!")
                return True
            except:
                continue
                
        raise AssertionError(f"Test {test_name} did not pass within {timeout} seconds")
    
    def expect_all_tests_complete(self, board, timeout=60):
        """Wait for all tests to complete."""
        board.serial.expect("All tests finished", timeout=timeout)
        logging.info("All kernel tests completed successfully!")