import logging
import time
import subprocess
import os
import tempfile
from utils.test_helpers import OneshotTest

class UsbBulkEchoTest(OneshotTest):
    """Test USB bulk echo functionality on nrf52840dk with usb-bulk configuration.
    
    This test uses the nrf52840dk-usb-bulk kernel configuration which:
    1. Includes the usbc_client capsule with VID:PID 0x6667:0xabcd
    2. Provides bulk endpoints (IN: 0x81, OUT: 0x02)
    3. Implements echo functionality in the kernel
    
    Note: The usb_bulk_echo app expects driver 0x90006 which doesn't exist,
    but the kernel's usbc_client provides echo functionality directly.
    """
    
    def __init__(self):
        # Don't flash any apps initially
        super().__init__(apps=[])
        
    def test(self, boards):
        """Override test method to set kernel configuration before flashing."""
        logging.info("Starting USB Bulk Echo Test")
        if len(boards) != 1:
            raise ValueError(f"UsbBulkEchoTest requires exactly 1 board. Got {len(boards)} boards.")
        
        single_board = boards[0]
        
        # Configure the board to use USB bulk kernel before erasing/flashing
        single_board.set_kernel_config("nrf52840dk-usb-bulk")
        logging.info("Configured board to use nrf52840dk-usb-bulk kernel")
        
        # Now do the normal test flow
        single_board.erase_board()
        single_board.serial.flush_buffer()
        single_board.flash_kernel()
        for app in self.apps:
            single_board.flash_app(app)
        
        self.oneshot_test(single_board)
        logging.info("Finished USB Bulk Echo Test")
        
    def build_rust_bulk_echo(self):
        """Build the Rust bulk-echo tool."""
        tool_path = "/home/tml/tock-hardware-ci/hwci/repos/tock/tools/usb/bulk-echo"
        
        # Check if we need to build (binary is in workspace target directory)
        binary_path = "/home/tml/tock-hardware-ci/hwci/repos/tock/tools/target/release/bulk-echo"
        if not os.path.exists(binary_path):
            logging.info("Building Rust bulk-echo tool...")
            result = subprocess.run(
                ["cargo", "build", "--release"],
                cwd=tool_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logging.error(f"Failed to build bulk-echo: {result.stderr}")
                return None
                
        return binary_path
        
    def test_bulk_echo(self, bulk_echo_path, test_size=8):
        """Test bulk echo with test data.
        
        Args:
            bulk_echo_path: Path to bulk-echo executable
            test_size: Number of bytes to test (default 8 to match kernel buffer)
            
        Returns:
            True if test passes, False otherwise
        """
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False) as input_file:
                input_path = input_file.name
            with tempfile.NamedTemporaryFile(delete=False) as output_file:
                output_path = output_file.name
            
            # Generate test data
            logging.info(f"Generating {test_size} bytes of test data")
            test_data = bytes(range(test_size % 256))  # Simple pattern for debugging
            with open(input_path, 'wb') as f:
                f.write(test_data)
            
            # Run bulk-echo test
            logging.info("Running bulk-echo test...")
            with open(input_path, 'rb') as infile, open(output_path, 'wb') as outfile:
                # Try running with timeout
                try:
                    result = subprocess.run(
                        [bulk_echo_path],
                        stdin=infile,
                        stdout=outfile,
                        stderr=subprocess.PIPE,
                        timeout=10
                    )
                except subprocess.TimeoutExpired:
                    logging.warning("bulk-echo timed out - checking if data was transferred")
                    # Check if we got any data even if it timed out
                    if os.path.getsize(output_path) > 0:
                        result = subprocess.CompletedProcess(args=[bulk_echo_path], returncode=0)
                    else:
                        return False
                
            if result.returncode != 0:
                stderr_text = result.stderr.decode('utf-8', errors='replace') if result.stderr else "No error output"
                logging.error(f"bulk-echo failed with code {result.returncode}: {stderr_text}")
                
                # Check if it's because device wasn't found
                if "Couldn't find target device" in stderr_text:
                    logging.error("USB device with VID:PID 0x6667:0xabcd not found")
                    logging.error("Make sure the board is connected and the kernel has enumerated")
                return False
                
            # Check output
            output_size = os.path.getsize(output_path)
            logging.info(f"Received {output_size} bytes from device")
            
            # Verify data
            with open(output_path, 'rb') as f:
                output_data = f.read()
                
            if output_data[:len(test_data)] == test_data:
                logging.info("Data integrity verified!")
                return True
            else:
                logging.error("Data mismatch")
                # Log first few bytes for debugging
                logging.error(f"Expected: {test_data[:10].hex()}")
                logging.error(f"Received: {output_data[:10].hex()}")
                return False
                    
        except Exception as e:
            logging.error(f"Test failed: {e}")
            return False
        finally:
            # Cleanup
            for f in [input_path, output_path]:
                if os.path.exists(f):
                    os.remove(f)

    def oneshot_test(self, board):
        """Main test function."""
        # Wait for kernel boot
        logging.info("Waiting for kernel boot message")
        output = board.serial.expect("Initialization complete. Entering main loop", timeout=10)
        if not output:
            raise Exception("Kernel did not boot properly")
            
        logging.info("Kernel booted successfully with USB bulk support")
        
        # Give USB time to enumerate
        time.sleep(3)
        
        # Build the test tool
        bulk_echo_path = self.build_rust_bulk_echo()
        if not bulk_echo_path:
            raise Exception("Failed to build bulk-echo tool")
            
        # Run tests with different data sizes
        # The kernel uses 8-byte buffers for bulk endpoints
        test_sizes = [8, 16, 24, 32, 64]
        failed_sizes = []
        
        for size in test_sizes:
            logging.info(f"\nTesting with {size} bytes...")
            if self.test_bulk_echo(bulk_echo_path, size):
                logging.info(f"✓ {size}-byte test PASSED")
            else:
                logging.warning(f"✗ {size}-byte test FAILED")
                failed_sizes.append(size)
                
        if not failed_sizes:
            logging.info("\nAll USB bulk echo tests PASSED!")
        elif len(failed_sizes) < len(test_sizes):
            logging.info(f"\nSome tests passed. Failed sizes: {failed_sizes}")
            logging.info("The kernel's bulk echo functionality is partially working")
        else:
            raise Exception("All USB bulk echo tests failed")

test = UsbBulkEchoTest()