import logging
import time
from utils.test_helpers import OneshotTest
import subprocess
import os
from boards.nrf52dk import Nrf52dk, get_board_serial


class BLECommunicationTest(OneshotTest):
    def __init__(self):
        # Initialize with no apps - we'll handle app flashing manually
        super().__init__(apps=[])

    def oneshot_test(self, board):
        """
        This test launches a second instance of the test framework to run the scanner
        while this instance runs the advertiser.
        """
        logging.info("Starting BLE Communication Test")

        # This board will be the advertiser
        advertiser_board = board
        advertiser_serial = get_board_serial(advertiser_board)
        logging.info(f"Using board with serial {advertiser_serial} as advertiser")

        # Start by flashing the advertiser
        logging.info("Setting up advertiser board...")
        advertiser_board.erase_board()
        advertiser_board.serial.flush_buffer()
        advertiser_board.flash_kernel()
        advertiser_board.flash_app("ble_advertising")

        # Check advertiser initialization
        logging.info("Verifying advertiser initialization...")
        adv_output = advertiser_board.serial.expect(
            "\\[Tutorial\\] BLE Advertising", timeout=10
        )
        if not adv_output:
            raise Exception("Advertiser did not initialize properly")

        # Wait for advertiser setup messages
        expected_adv_messages = [
            " - Initializing BLE... TockOS",
            " - Setting the device name... TockOS",
            " - Setting the device UUID...",
            " - Setting manufacturer data...",
            " - Setting service data...",
            " - Begin advertising! TockOS",
            "Now advertising every 300 ms as 'TockOS'",
        ]

        for msg in expected_adv_messages:
            output = advertiser_board.serial.expect(msg, timeout=10)
            if not output:
                raise Exception(f"Advertiser setup failed at step: {msg}")
            logging.info(f"Advertiser: {msg}")

        logging.info(
            "Advertiser is now running. Starting scanner in separate process..."
        )

        # Get the path to the scanner test module
        current_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(current_dir, "..", "core", "main.py")
        scanner_test = os.path.join(current_dir, "ble_scanning_verify.py")

        # Create a temporary configuration file for the scanner
        config_path = os.path.join(current_dir, "scanner_config.yaml")
        with open(config_path, "w") as f:
            f.write(f"exclude_serial: {advertiser_serial}\n")

        # Launch the scanner process with configuration
        scanner_process = subprocess.Popen(
            [
                "python3",
                main_script,
                "--board",
                "boards/nrf52dk.py",
                "--test",
                scanner_test,
                "--config",
                config_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            stdout, stderr = scanner_process.communicate(timeout=60)

            if scanner_process.returncode != 0:
                logging.error("Scanner process failed")
                logging.error(f"Scanner stdout: {stdout.decode()}")
                logging.error(f"Scanner stderr: {stderr.decode()}")
                raise Exception("Scanner process failed to complete successfully")

            logging.info("Scanner process completed successfully")
            logging.info("BLE Communication Test completed successfully")

        except subprocess.TimeoutExpired:
            scanner_process.kill()
            raise Exception("Scanner process timed out")

        finally:
            # Clean up config file
            if os.path.exists(config_path):
                os.remove(config_path)
            # Ensure scanner process is terminated
            if scanner_process.poll() is None:
                scanner_process.kill()
