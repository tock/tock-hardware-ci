# hwci/tests/ble_advertising_scanning_test.py

import logging
import time
from core.test_harness import TestHarness


class BleAdvertisingScanningTest(TestHarness):
    """
    Multi-board test:
    - Board 0: ble_advertising
    - Board 1: ble_passive_scanning
    We confirm that the advertiser prints "Now advertising..."
    and that the scanner detects our specific advertisement data.
    """

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
        #   "ble_advertising" is the path to your ble_advertising directory in libtock-c
        #   "ble_passive_scanning" is the path to your ble_passive_scanning directory
        advertiser.flash_app("ble_advertising")
        scanner.flash_app("ble_passive_scanning")

        logging.info(
            "Flashed ble_advertising -> board0, ble_passive_scanning -> board1."
        )

        # We want to see certain lines from each board. We'll read them in a loop:
        # Because both boards may print interleaved, we'll poll each board's serial.
        # We'll store flags once we've seen the key lines.

        adv_done = False  # Did we see the "Now advertising every..."
        scan_done = False  # Did we see scanner detect our specific advertisement?

        # Keep track of specific advertisement patterns we're looking for
        manufacturer_data_found = False  # 0x13, 0x37
        device_name_found = False  # "TockOS"

        # To track PDU type for the current advertisement being processed
        current_pdu_type = None

        # For tracking multi-line advertisement data
        processing_adv_data = False
        current_address = None
        current_data = None

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
                if "[Tutorial] BLE Advertising" in text_adv:
                    adv_tutorial_line = True
                if "Now advertising every" in text_adv:
                    adv_done = True

            # Read from scanner's console if any new line is present
            line_scan = scanner.serial.expect(".+\r?\n", timeout=1, timeout_error=False)
            if line_scan:
                text_scan = line_scan.decode("utf-8", errors="replace").strip()
                logging.debug(f"[Scanner] {text_scan}")

                # Track beginning and end of advertisement list
                if (
                    "--------------------------LIST-------------------------"
                    in text_scan
                ):
                    processing_adv_data = True
                    continue

                if (
                    "--------------------------END---------------------------"
                    in text_scan
                ):
                    processing_adv_data = False
                    continue

                if not processing_adv_data:
                    # Skip lines outside of an advertisement list
                    if "[Tutorial] BLE Passive Scanner" in text_scan:
                        scan_tutorial_line = True
                    continue

                # Process advertisement data
                if "PDU Type:" in text_scan:
                    # Start of a new advertisement
                    current_pdu_type = text_scan.split("PDU Type:")[1].strip()
                    # Reset tracking for this advertisement
                    current_address = None
                    current_data = None

                elif "Address:" in text_scan:
                    current_address = text_scan.split("Address:")[1].strip()

                elif "Data:" in text_scan:
                    current_data = text_scan.split("Data:")[1].strip()

                    # If we have a complete advertisement entry, check it
                    if current_pdu_type and current_data:
                        # Reset for next advertisement entry
                        logging.debug(
                            f"Checking advertisement - Type: {current_pdu_type}, Data: {current_data}"
                        )

                        # Look for specific data patterns from our advertiser

                        # Manufacturer data: 0x13, 0x37
                        # It appears in the data as "ff" (manufacturer data type) followed by "13 37"
                        if "ff" in current_data and "13 37" in current_data:
                            logging.info(
                                "Found manufacturer data (13 37) in advertisement!"
                            )
                            manufacturer_data_found = True

                        # Device name: "TockOS"
                        # It should appear after the device name type code "09"
                        # ASCII for "TockOS" is: 54 6f 63 6b 4f 53
                        # But the data may be shortened, so look for parts of it
                        if "09" in current_data and any(
                            name_part in current_data
                            for name_part in ["54 6f 63 6b", "54 6f 63", "54 6f"]
                        ):
                            logging.info("Found device name (TockOS) in advertisement!")
                            device_name_found = True

                        # Mark scan as done if we found sufficient evidence this is our advertisement
                        if (
                            manufacturer_data_found or device_name_found
                        ) and "NON_CONNECT_IND" in current_pdu_type:
                            scan_done = True

                # Alternative approach: look for specific patterns in raw output
                if ("NON_CONNECT_IND" in text_scan) and not scan_done:
                    logging.info("Found NON_CONNECT_IND advertisement, will check data")

            if adv_done and scan_done:
                # We have everything we need
                break

        # Check if both boards printed the expected lines
        if not adv_done:
            raise Exception(
                "Advertiser board never printed \"Now advertising every ... ms as 'TockOS'\"!"
            )

        # Provide a more specific error if we didn't find our advertisement
        if not scan_done:
            error_msg = "Scanner did not detect our specific advertisement data!"
            if manufacturer_data_found:
                error_msg += (
                    " (Found manufacturer data but not in NON_CONNECT_IND type)"
                )
            elif device_name_found:
                error_msg += " (Found device name but not in NON_CONNECT_IND type)"
            else:
                error_msg += " No identifying patterns found in any advertisements."
            raise Exception(error_msg)

        logging.info("BLE advertising + scanning test passed successfully!")
        if manufacturer_data_found:
            logging.info(
                "✓ Verified advertisement contained correct manufacturer data (13 37)"
            )
        if device_name_found:
            logging.info("✓ Verified advertisement contained device name (TockOS)")


test = BleAdvertisingScanningTest()
