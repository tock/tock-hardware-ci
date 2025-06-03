import logging
import time
import serial
import serial.tools.list_ports
from utils.test_helpers import OneshotTest

class UsbCdcTest(OneshotTest):
    """Test USB CDC functionality on nrf52840dk with test-usb configuration.
    
    This test verifies that:
    1. The kernel boots successfully with USB CDC enabled
    2. USB CDC device enumerates on the host
    3. Data can be sent and received through the USB CDC interface
    """
    
    def __init__(self):
        # Don't flash any apps initially
        super().__init__(apps=[])
        
    def find_usb_cdc_port(self, vid=0x1915, pid=0x503a, timeout=10):
        """Find the USB CDC port for the Nordic nRF52840DK.
        
        Args:
            vid: USB Vendor ID (0x1915 for Nordic Semiconductor)
            pid: USB Product ID (0x503a for nRF52840DK CDC)
            timeout: Maximum time to wait for device enumeration
            
        Returns:
            Serial port device path or None if not found
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.vid == vid and port.pid == pid:
                    logging.info(f"Found USB CDC device at {port.device} (VID:PID = {vid:04x}:{pid:04x})")
                    return port.device
            time.sleep(0.5)
            
        return None
        
    def test_usb_cdc_echo(self, usb_port):
        """Test USB CDC echo functionality.
        
        Args:
            usb_port: Serial port device path
            
        Returns:
            True if test passes, False otherwise
        """
        try:
            # Open USB CDC port
            with serial.Serial(usb_port, baudrate=115200, timeout=2) as usb_serial:
                logging.info(f"Opened USB CDC port {usb_port}")
                
                # Clear any buffered data
                usb_serial.reset_input_buffer()
                usb_serial.reset_output_buffer()
                
                # Send test messages and verify echo
                test_messages = [
                    b"Hello USB CDC!\n",
                    b"Testing 123\n",
                    b"abcdefghijklmnopqrstuvwxyz\n",
                    b"0123456789\n",
                    b"Special chars: !@#$%^&*()\n"
                ]
                
                for msg in test_messages:
                    logging.info(f"Sending: {msg.decode('utf-8', errors='replace').strip()}")
                    usb_serial.write(msg)
                    
                    # Read back the echo
                    response = usb_serial.readline()
                    logging.info(f"Received: {response.decode('utf-8', errors='replace').strip()}")
                    
                    if response != msg:
                        logging.error(f"Echo mismatch! Sent: {msg}, Received: {response}")
                        return False
                        
                logging.info("All echo tests passed!")
                return True
                
        except Exception as e:
            logging.error(f"USB CDC test failed: {e}")
            return False

    def oneshot_test(self, board):
        """Main test function."""
        # First verify kernel boots with USB enabled
        logging.info("Waiting for kernel boot message with USB enabled")
        output = board.serial.expect("Initialization complete. Entering main loop", timeout=10)
        if not output:
            raise Exception("Kernel did not boot properly with USB enabled")
            
        logging.info("Kernel booted successfully with USB CDC enabled")
        
        # Give USB time to enumerate
        time.sleep(2)
        
        # Find the USB CDC port
        usb_port = self.find_usb_cdc_port()
        if not usb_port:
            raise Exception("USB CDC device not found. Make sure the board is connected via USB.")
            
        # Now flash and run the c_hello app to test console over USB
        logging.info("Flashing c_hello app to test console output over USB CDC")
        board.flash_app("c_hello")
        
        # Test USB CDC echo functionality using the console
        if not self.test_usb_cdc_echo(usb_port):
            raise Exception("USB CDC echo test failed")
            
        # Also verify we can see the app output on the USB console
        try:
            with serial.Serial(usb_port, baudrate=115200, timeout=5) as usb_serial:
                # Reset the board to trigger app output
                board.reset()
                
                # Look for c_hello output on USB console
                usb_serial.reset_input_buffer()
                found_hello = False
                
                start_time = time.time()
                while time.time() - start_time < 5:
                    line = usb_serial.readline()
                    if line:
                        decoded = line.decode('utf-8', errors='replace')
                        logging.info(f"USB console: {decoded.strip()}")
                        if "Hello World" in decoded:
                            found_hello = True
                            break
                            
                if not found_hello:
                    raise Exception("Did not see 'Hello World' output on USB console")
                    
                logging.info("Successfully verified app console output over USB CDC")
                
        except Exception as e:
            logging.error(f"Failed to verify app output on USB console: {e}")
            raise
            
        logging.info("USB CDC test completed successfully!")

test = UsbCdcTest()