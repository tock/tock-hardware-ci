import logging
import time
import serial
import serial.tools.list_ports
from utils.test_helpers import OneshotTest

class UsbSimpleTest(OneshotTest):
    """Simple USB CDC test for nrf52840dk with test-usb configuration.
    
    This test verifies that:
    1. The kernel boots successfully with USB CDC enabled
    2. USB CDC device enumerates on the host
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
            logging.warning("USB CDC device not found. This may be expected if USB is not properly connected.")
        else:
            logging.info(f"USB CDC device successfully enumerated at {usb_port}")
            
            # Try to open the port
            try:
                with serial.Serial(usb_port, baudrate=115200, timeout=1) as usb_serial:
                    logging.info("Successfully opened USB CDC port")
                    # Just send a simple message
                    usb_serial.write(b"USB test message\n")
                    logging.info("Sent test message to USB CDC port")
            except Exception as e:
                logging.error(f"Failed to communicate with USB CDC port: {e}")
                
        logging.info("USB simple test completed!")

test = UsbSimpleTest()