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
    EXPECTED_PDU_TYPE = "NON_CONNECT_IND"
    EXPECTED_MANUFACTURER_DATA = (
        "13 37"  # From the advertiser's manufacturer_data[] = {0x13, 0x37}
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

                # Store any discovered advertisement for later analysis
                if self.EXPECTED_PDU_TYPE in text_scan:
                    received_advertisements.append(text_scan)

                    # See if this advertisement has our expected characteristics
                    adv_matches = (
                        # Check for the expected PDU type
                        self.EXPECTED_PDU_TYPE in text_scan
                        and
                        # Check for the manufacturer data
                        self.EXPECTED_MANUFACTURER_DATA in text_scan
                    )

                    if adv_matches:
                        logging.info("Scanner detected our expected advertisement")
                        scan_done = True

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
                f"Manufacturer data: {self.EXPECTED_MANUFACTURER_DATA}\n"
            )

            if received_advertisements:
                error_detail += "\nReceived advertisements:\n"
                for i, adv in enumerate(received_advertisements, 1):
                    # Extract and display just the relevant parts of the advertisement
                    error_detail += f"- Adv #{i}: {adv[:200]}...\n"
            else:
                error_detail += "No advertisements were detected by the scanner!"

            error_messages.append(error_detail)

        # Raise an exception with all error details if there were any failures
        if error_messages:
            raise Exception("\n".join(error_messages))

        logging.info("BLE advertising + scanning test passed successfully!")


test = BleAdvertisingScanningTest()
