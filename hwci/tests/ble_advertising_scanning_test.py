# hwci/tests/ble_advertising_scanning_test.py

import logging
import time
import re
from core.test_harness import TestHarness


class BleAdvertisingScanningTest(TestHarness):
    """
    Multi-board test:
    - Board 0: ble_advertising
    - Board 1: ble_passive_scanning

    We confirm that the advertiser prints "Now advertising..."
    and that the scanner detects the specific advertisement from our advertiser.

    The test validates:
    1. The advertiser successfully advertises with the expected device name
    2. The scanner detects the advertiser's specific advertisement
    3. The advertisement contains the expected data payload
    """

    # Configuration constants for test validation
    EXPECTED_DEVICE_NAME = "TockOS"
    EXPECTED_PDU_TYPE = "2 NON_CONNECT_IND"  # Modified to include the numeric type (2)

    # The manufacturer data pattern in the advertisement data
    # In BLE, manufacturer data is preceded by a length byte, 0xFF type byte,
    # then possibly company ID bytes, then the actual data
    MANUFACTURER_DATA_PATTERN = (
        r"ff.*?13 37"  # Look for FF followed by 13 37 anywhere in the data
    )

    # Pattern to extract BLE address from log output
    ADDR_PATTERN = r"Address: ([0-9a-fA-F]{2} [0-9a-fA-F]{2} [0-9a-fA-F]{2} [0-9a-fA-F]{2} [0-9a-fA-F]{2} [0-9a-fA-F]{2})"

    # Pattern to extract device name from advertisement data
    DEVICE_NAME_PATTERN = (
        r"TockOS"  # Simplified pattern - could be enhanced to extract from actual data
    )

    def test(self, boards):
        if len(boards) < 2:
            raise ValueError(
                "Need at least 2 boards for BLE advertising/scanning test!"
            )

        advertiser = boards[0]
        scanner = boards[1]

        # Check that we're not using the same serial port for both boards
        if advertiser.uart_port == scanner.uart_port:
            raise ValueError(
                f"Both boards are using the same serial port: {advertiser.uart_port}. "
                f"Each board must have a unique serial port. "
                f"Board 1 SN: {getattr(advertiser, 'serial_number', 'unknown')}, "
                f"Board 2 SN: {getattr(scanner, 'serial_number', 'unknown')}"
            )

        # Log the selected ports for debugging
        logging.info(
            f"Advertiser (SN: {advertiser.serial_number}) using port: {advertiser.uart_port}"
        )
        logging.info(
            f"Scanner (SN: {scanner.serial_number}) using port: {scanner.uart_port}"
        )

        # Erase & reflash the kernel on both boards:
        advertiser.erase_board()
        scanner.erase_board()
        advertiser.serial.flush_buffer()
        scanner.serial.flush_buffer()

        advertiser.flash_kernel()
        scanner.flash_kernel()

        # Flash user apps:
        advertiser.flash_app("ble_advertising")
        scanner.flash_app("ble_passive_scanning")

        logging.info(
            "Flashed ble_advertising -> board0, ble_passive_scanning -> board1."
        )

        # We want to see certain lines from each board. We'll read them in a loop:
        # Because both boards may print interleaved, we'll poll each board's serial.
        # We'll store flags once we've seen the key lines.

        adv_done = False  # Did we see the "Now advertising every..."
        scan_done = False  # Did we see scanner output for our specific advertisement?

        # To store information for validation and error reporting
        advertiser_addr = None  # Will store the advertiser's BLE address if found
        received_advertisements = []  # Will store all advertisements found by scanner
        # For collecting multi-line advertisement data
        current_adv = []
        collecting_adv = False

        start_time = time.time()
        TIMEOUT = 30  # total seconds to wait

        while True:
            if time.time() - start_time > TIMEOUT:
                break

            # Read from advertiser's console if any new line is present
            line_adv = advertiser.serial.expect(
                ".+\r?\n", timeout=1, timeout_error=False
            )
            if line_adv:
                text_adv = line_adv.decode("utf-8", errors="replace").strip()
                logging.debug(f"[Advertiser] {text_adv}")

                # Detect when advertising starts
                if (
                    "Now advertising every" in text_adv
                    and self.EXPECTED_DEVICE_NAME in text_adv
                ):
                    adv_done = True
                    logging.info(
                        f"Advertiser started advertising as '{self.EXPECTED_DEVICE_NAME}'"
                    )

            # Read from scanner's console if any new line is present
            line_scan = scanner.serial.expect(".+\r?\n", timeout=1, timeout_error=False)
            if line_scan:
                text_scan = line_scan.decode("utf-8", errors="replace").strip()
                logging.debug(f"[Scanner] {text_scan}")

                # Start collecting an advertisement when we see PDU Type
                if "PDU Type:" in text_scan:
                    collecting_adv = True
                    current_adv = [text_scan]
                # Continue collecting the advertisement
                elif collecting_adv and "Data:" in text_scan:
                    current_adv.append(text_scan)
                # End of the advertisement list
                elif collecting_adv and "--------------------------END" in text_scan:
                    collecting_adv = False
                    # Join the collected lines into a single string for analysis
                    complete_adv = "\n".join(current_adv)
                    received_advertisements.append(complete_adv)

                    # Check if this advertisement matches our criteria
                    pdu_type_match = (
                        f"PDU Type: {self.EXPECTED_PDU_TYPE}" in complete_adv
                    )
                    manufacturer_data_match = re.search(
                        self.MANUFACTURER_DATA_PATTERN, complete_adv
                    )

                    if pdu_type_match and manufacturer_data_match:
                        logging.info(
                            f"Scanner detected our expected advertisement: \n{complete_adv}"
                        )
                        scan_done = True
                # Add other advertisement lines while collecting
                elif collecting_adv:
                    current_adv.append(text_scan)

            if adv_done and scan_done:
                # We have everything we need
                break

        # Generate detailed error messages if needed
        error_messages = []

        if not adv_done:
            error_messages.append(
                f"Advertiser board never printed \"Now advertising every ... ms as '{self.EXPECTED_DEVICE_NAME}'\"!"
            )

        if not scan_done:
            # Build a more detailed error message
            error_detail = (
                f"Scanner board never detected the expected advertisement.\n"
                f"Expected: PDU Type: {self.EXPECTED_PDU_TYPE}, "
                f"Manufacturer data pattern: {self.MANUFACTURER_DATA_PATTERN}\n"
            )

            if received_advertisements:
                error_detail += "\nReceived advertisements (first 3 shown):\n"
                for i, adv in enumerate(received_advertisements[:3], 1):
                    # Show the full advertisement for better debugging
                    error_detail += f"- Adv #{i}:\n{adv}\n\n"
            else:
                error_detail += "No advertisements were detected by the scanner!"

            error_messages.append(error_detail)

        # Raise an exception with all error details if there were any failures
        if error_messages:
            raise Exception("\n".join(error_messages))

        logging.info("BLE advertising + scanning test passed successfully!")


test = BleAdvertisingScanningTest()
