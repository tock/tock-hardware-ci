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

    # Regular‑expression version so we’re resilient to variable whitespace
    MANUFACTURER_DATA_RE = re.compile(r"\b13\s+37\b", re.IGNORECASE)

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

        adv_done = False  # Did we see the advertiser start advertising?

        scan_done = False  # Did we see scanner output for our specific advertisement?

        # Store all scanner output for easier debugging and analysis
        scanner_output = []
        advertiser_output = []

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
                advertiser_output.append(text_adv)
                logging.debug(f"[Advertiser] {text_adv}")

                # Detect when the advertiser starts.  Depending on libtock‑rs
                # version we may get either of the lines below; a single regex
                # covers both and survives harmless wording tweaks.
                if re.search(
                    rf"(Now advertising .*'{self.EXPECTED_DEVICE_NAME}'|"
                    rf"Begin advertising!? *{self.EXPECTED_DEVICE_NAME})",
                    text_adv,
                ):

                    adv_done = True
                    logging.info(
                        f"Advertiser started advertising as '{self.EXPECTED_DEVICE_NAME}'"
                    )

            # Read from scanner's console if any new line is present
            line_scan = scanner.serial.expect(".+\r?\n", timeout=1, timeout_error=False)
            if line_scan:
                text_scan = line_scan.decode("utf-8", errors="replace").strip()
                scanner_output.append(text_scan)
                logging.debug(f"[Scanner] {text_scan}")

                # Look for “13 37” with flexible spacing
                if self.MANUFACTURER_DATA_RE.search(text_scan):
                    logging.info(
                        f"Scanner detected our expected manufacturer data: {self.MANUFACTURER_DATA}"
                    )
                    scan_done = True

            if adv_done and scan_done:
                # We have everything we need
                break

        # Look at the combined output to find advertisements with our manufacturer data
        full_scanner_output = "\n".join(scanner_output)
        logging.info(f"Collected {len(scanner_output)} lines from scanner")

        # Even if we didn't find it during line-by-line scanning, check the full output
        if not scan_done and self.MANUFACTURER_DATA_RE.search(full_scanner_output):

            logging.info(f"Found manufacturer data in combined scanner output")
            scan_done = True

        # Generate detailed error messages if needed
        error_messages = []

        if not adv_done:
            error_messages.append(
                f"Advertiser board never printed \"Now advertising every ... ms as '{self.EXPECTED_DEVICE_NAME}'\"!"
            )

        if not scan_done:
            # Print a useful diagnostic showing all the data fields seen
            data_fields = re.findall(r"Data: ([0-9a-fA-F ]+)", full_scanner_output)

            error_detail = (
                f"Scanner board never detected the expected advertisement.\n"
                f"Looking for manufacturer data: {self.MANUFACTURER_DATA}\n"
            )

            if data_fields:
                error_detail += "\nData fields seen in advertisements:\n"
                for i, data in enumerate(
                    data_fields[:10], 1
                ):  # Show first 10 data fields
                    error_detail += f"- {i}: {data}\n"
                if len(data_fields) > 10:
                    error_detail += (
                        f"... and {len(data_fields) - 10} more data fields\n"
                    )
            else:
                error_detail += "No data fields were found in the scanner output!\n"

            # Add a small sample of the scanner output for debugging
            error_detail += "\nSample of scanner output:\n"
            sample_size = min(20, len(scanner_output))  # Show up to 20 lines
            error_detail += "\n".join(scanner_output[:sample_size])
            if len(scanner_output) > sample_size:
                error_detail += (
                    f"\n... and {len(scanner_output) - sample_size} more lines"
                )

            error_messages.append(error_detail)

        # Raise an exception with all error details if there were any failures
        if error_messages:
            raise Exception("\n".join(error_messages))

        logging.info("BLE advertising + scanning test passed successfully!")


test = BleAdvertisingScanningTest()
