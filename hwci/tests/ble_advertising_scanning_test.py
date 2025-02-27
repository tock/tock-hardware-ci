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
    and that the scanner prints a discovered advertisement.
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
        scan_done = False  # Did we see scanner output a discovered advertisement?

        # Optional: look for [Tutorial] lines as well
        adv_tutorial_line = False
        scan_tutorial_line = False

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
                if "[Tutorial] BLE Passive Scanner" in text_scan:
                    scan_tutorial_line = True
                if (
                    "--------------------------LIST-------------------------"
                    in text_scan
                ):
                    # The next few lines might contain "PDU Type: 2 NON_CONNECT_IND"
                    # We'll see if that appears eventually
                    pass
                if "NON_CONNECT_IND" in text_scan:
                    scan_done = True

            if adv_done and scan_done:
                # We have everything we need
                break

        # Check if both boards printed the expected lines
        if not adv_done:
            raise Exception(
                "Advertiser board never printed \"Now advertising every ... ms as 'TockOS'\"!"
            )
        if not scan_done:
            raise Exception(
                "Scanner board never saw a NON_CONNECT_IND advertisement in its list output!"
            )

        logging.info("BLE advertising + scanning test passed successfully!")


test = BleAdvertisingScanningTest()
