#!/usr/bin/env python3

"""
Kernel MPU Tests

This test runs the kernel-level MPU tests that verify memory protection
boundaries without requiring userspace.
"""

from tests.kernel_test_base import KernelTestHarness
import logging
import re

class KernelMpuTest(KernelTestHarness):
    """Test kernel-level MPU functionality."""
    
    # Use our new kernel test configuration
    KERNEL_CONFIG = "kernel-test"
    
    # Expected tests to run
    EXPECTED_TESTS = [
        "test_mpu_basic_configuration",
        "test_mpu_region_boundaries", 
        "test_mpu_flash_protection",
        "test_mpu_peripheral_isolation",
        "test_mpu_overlapping_regions",
        "test_mpu_null_pointer_protection",
        "test_mpu_fault_handling",
        "test_mpu_process_isolation"
    ]
    
    def monitor_test_output(self, board):
        """Monitor test output from our kernel test framework."""
        passed_tests = []
        failed_tests = []
        
        # Wait for test suite to start
        board.serial.expect(r"\[TEST\] Starting kernel test suite", timeout=10)
        logging.info("Kernel test suite started")
        
        # Monitor individual test results
        timeout = 60
        start_time = board.serial.timeout_start()
        
        while board.serial.elapsed_time(start_time) < timeout:
            try:
                line = board.serial.readline(timeout=1)
                
                # Check for test execution
                if "[TEST] Running" in line:
                    match = re.search(r"\[TEST\] Running (.+)", line)
                    if match:
                        test_name = match.group(1).strip()
                        logging.info(f"Running test: {test_name}")
                
                # Check for test pass
                elif "[PASS]" in line:
                    match = re.search(r"\[PASS\] (.+)", line)
                    if match:
                        test_name = match.group(1).strip()
                        passed_tests.append(test_name)
                        logging.info(f"Test passed: {test_name}")
                
                # Check for test failure
                elif "[FAIL]" in line:
                    match = re.search(r"\[FAIL\] (.+)", line)
                    if match:
                        failure_info = match.group(1).strip()
                        if ":" in failure_info:
                            test_name, error = failure_info.split(":", 1)
                        else:
                            test_name = failure_info
                            error = "Unknown error"
                        failed_tests.append((test_name.strip(), error.strip()))
                        logging.error(f"Test failed: {test_name} - {error}")
                
                # Check for suite completion
                elif "[TEST] Test suite complete" in line:
                    match = re.search(r"(\d+) passed, (\d+) failed", line)
                    if match:
                        total_passed = int(match.group(1))
                        total_failed = int(match.group(2))
                        logging.info(f"Test suite complete: {total_passed} passed, {total_failed} failed")
                    break
                    
            except:
                continue
        
        # Verify expected tests ran
        ran_tests = set(passed_tests + [t[0] for t in failed_tests])
        expected = set(self.EXPECTED_TESTS)
        missing = expected - ran_tests
        
        if missing:
            raise AssertionError(f"Expected tests did not run: {missing}")
        
        # Check for failures
        if failed_tests:
            failures = "\n".join([f"  - {name}: {error}" for name, error in failed_tests])
            raise AssertionError(f"Kernel MPU tests failed:\n{failures}")
        
        logging.info(f"All {len(passed_tests)} MPU tests passed!")

# Create test instance
test = KernelMpuTest()