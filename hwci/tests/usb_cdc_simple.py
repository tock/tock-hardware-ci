import logging
import time
import serial
import serial.tools.list_ports
from utils.test_helpers import OneshotTest

class UsbCdcSimpleTest(OneshotTest):
    """Simple test to verify USB CDC functionality on nrf52840dk with test-usb configuration.
    
    This test verifies that:
    1. The kernel boots successfully with USB CDC enabled
    2. USB CDC device enumerates on the host (VID:PID 0x1915:0x503a)
    
    This is suitable for the nrf52840dk-test-usb configuration which provides
    CDC-ACM (serial over USB) but not bulk endpoints.
    """
    
    def __init__(self):
        # Don't flash any apps, just test kernel USB functionality
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
                    logging.info(f"Found USB CDC device at {port.device}")
                    logging.info(f"  VID:PID = {vid:04x}:{pid:04x}")
                    logging.info(f"  Manufacturer: {port.manufacturer}")
                    logging.info(f"  Product: {port.product}")
                    logging.info(f"  Serial: {port.serial_number}")
                    return port.device
            time.sleep(0.5)
            
        return None
    
    def oneshot_test(self, board):
        """Main test function."""
        # First verify kernel boots with USB enabled
        logging.info("Waiting for kernel boot message with USB CDC enabled")
        output = board.serial.expect("Initialization complete. Entering main loop", timeout=10)
        if not output:
            raise Exception("Kernel did not boot properly with USB enabled")
            
        logging.info("Kernel booted successfully with USB CDC enabled")
        
        # Give USB time to enumerate
        time.sleep(2)
        
        # Find the USB CDC port
        logging.info("Looking for USB CDC device...")
        usb_port = self.find_usb_cdc_port()
        if not usb_port:
            raise Exception("USB CDC device not found. Make sure the board is connected via USB.")
            
        logging.info(f"USB CDC device successfully enumerated at {usb_port}")
            
        # Try to open the port and send a simple message
        try:
            logging.info("Testing USB CDC communication...")
            with serial.Serial(usb_port, baudrate=115200, timeout=2) as usb_serial:
                logging.info("Successfully opened USB CDC port")
                
                # Send a test message
                test_msg = b"USB CDC test message\r\n"
                usb_serial.write(test_msg)
                logging.info("Sent test message to USB CDC port")
                
                # Try to read something back (might be echo or kernel messages)
                usb_serial.reset_input_buffer()
                time.sleep(0.5)
                
                # Send another message and check if we can read anything
                usb_serial.write(b"\r\n")
                time.sleep(0.5)
                
                data = usb_serial.read(100)  # Read up to 100 bytes
                if data:
                    logging.info(f"Received {len(data)} bytes from USB CDC")
                    decoded = data.decode('utf-8', errors='replace')
                    logging.info(f"Data preview: {decoded[:50]}...")
                else:
                    logging.info("No data received, but port is operational")
                
                logging.info("USB CDC communication test completed successfully")
                
        except Exception as e:
            logging.error(f"Failed to communicate with USB CDC port: {e}")
            raise
                
        logging.info("USB CDC test PASSED!")

test = UsbCdcSimpleTest()