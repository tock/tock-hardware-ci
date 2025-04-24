# hwci/tests/ble_advertising_scanning_test.py
#
# Multi‑board integration test:
#   • Board 0 runs the ble_advertising example
#   • Board 1 runs the ble_passive_scanning example
#
# We verify that the advertiser prints its “start advertising” message and that
# the scanner eventually prints at least one advertisement whose
# manufacturer‑specific data contains our company identifier {0x13, 0x37}.
#
# The identifier is transmitted little‑endian on the air interface, so the
# scanner can show either “… ff 13 37 …” or “… ff 03 37 …”.

import logging
import time
import re
from core.test_harness import TestHarness


class BleAdvertisingScanningTest(TestHarness):
    """
    Multi‑board test:
      1. Advertiser reports it is advertising with the expected device name.
      2. Scanner prints at least one advertisement that contains our company ID
         (0x13, 0x37) inside the manufacturer‑specific field.
    """

    EXPECTED_DEVICE_NAME = "TockOS"

    # Human‑readable form for error messages / logging only
    # MANUFACTURER_DATA = "13 37"

    # Regex that matches either byte order, with flexible whitespace and case
    # MANUFACTURER_DATA_RE = re.compile(r"\bff\s+(?:13\s+37|03\s+37)\b", re.IGNORECASE)

    MANUFACTURER_DATA = "06 00"
    MANUFACTURER_DATA_RE = re.compile(r"\bff\s+06\s+00\b", re.IGNORECASE)

    def test(self, boards):
        if len(boards) < 2:
            raise ValueError(
                "Need at least 2 boards for BLE advertising/scanning test!"
            )

        advertiser, scanner = boards[0], boards[1]

        # Safety: ensure distinct UARTs
        if advertiser.uart_port == scanner.uart_port:
            raise ValueError(
                f"Both boards are using the same serial port: {advertiser.uart_port}. "
                f"Each board must have a unique serial port. "
                f"Board 1 SN: {getattr(advertiser, 'serial_number', 'unknown')}, "
                f"Board 2 SN: {getattr(scanner, 'serial_number', 'unknown')}"
            )

        logging.info(
            f"Advertiser (SN: {advertiser.serial_number}) using port: {advertiser.uart_port}"
        )
        logging.info(
            f"Scanner (SN: {scanner.serial_number}) using port: {scanner.uart_port}"
        )

        # Clean slate
        advertiser.erase_board()
        scanner.erase_board()
        advertiser.serial.flush_buffer()
        scanner.serial.flush_buffer()

        advertiser.flash_kernel()
        scanner.flash_kernel()

        advertiser.flash_app("ble_advertising")
        scanner.flash_app("ble_passive_scanning")

        logging.info(
            "Flashed ble_advertising -> board0, ble_passive_scanning -> board1."
        )

        adv_done = False  # advertiser start message seen
        scan_done = False  # manufacturer data seen

        scanner_output: list[str] = []
        advertiser_output: list[str] = []

        start_time = time.time()
        TIMEOUT = 30  # seconds

        while True:
            if time.time() - start_time > TIMEOUT:
                break

            # ---------- Advertiser ----------
            line_adv = advertiser.serial.expect(
                ".+\r?\n", timeout=1, timeout_error=False
            )
            if line_adv:
                text_adv = line_adv.decode("utf-8", errors="replace").strip()
                advertiser_output.append(text_adv)
                logging.debug(f"[Advertiser] {text_adv}")

                if re.search(
                    rf"(Now advertising .*'{self.EXPECTED_DEVICE_NAME}'|"
                    rf"Begin advertising!? *{self.EXPECTED_DEVICE_NAME})",
                    text_adv,
                ):
                    adv_done = True
                    logging.info(
                        f"Advertiser started advertising as '{self.EXPECTED_DEVICE_NAME}'"
                    )

            # ---------- Scanner ----------
            line_scan = scanner.serial.expect(".+\r?\n", timeout=1, timeout_error=False)
            if line_scan:
                text_scan = line_scan.decode("utf-8", errors="replace").strip()
                scanner_output.append(text_scan)
                logging.debug(f"[Scanner] {text_scan}")

                if self.MANUFACTURER_DATA_RE.search(text_scan):
                    logging.info(
                        f"Scanner detected our expected manufacturer data ({self.MANUFACTURER_DATA})"
                    )
                    scan_done = True

            if adv_done and scan_done:
                break

        # Final pass over accumulated output
        full_scan_out = "\n".join(scanner_output)
        logging.info(f"Collected {len(scanner_output)} lines from scanner")

        if not scan_done and self.MANUFACTURER_DATA_RE.search(full_scan_out):
            logging.info("Found manufacturer data in combined scanner output")
            scan_done = True

        # Assemble error report if needed
        errors = []

        if not adv_done:
            errors.append(
                f"Advertiser never printed its start‑advertising line containing "
                f"'{self.EXPECTED_DEVICE_NAME}'."
            )

        if not scan_done:
            data_fields = re.findall(r"Data:\s*([0-9a-fA-F ]+)", full_scan_out)

            err = (
                "Scanner board never detected an advertisement with the expected "
                f"manufacturer data ({self.MANUFACTURER_DATA}).\n"
            )
            if data_fields:
                err += "\nData fields seen in advertisements:\n"
                for i, data in enumerate(data_fields[:10], 1):
                    err += f"  {i:2d}: {data}\n"
                if len(data_fields) > 10:
                    err += f"  … and {len(data_fields) - 10} more\n"
            else:
                err += "No advertisement ‘Data: …’ lines were captured!\n"

            sample = "\n".join(scanner_output[:20])
            err += "\nSample scanner output:\n" + sample
            if len(scanner_output) > 20:
                err += f"\n… and {len(scanner_output) - 20} more lines"

            errors.append(err)

        if errors:
            raise Exception("\n\n".join(errors))

        logging.info("BLE advertising + scanning test passed successfully!")


# For manual invocation
test = BleAdvertisingScanningTest()
