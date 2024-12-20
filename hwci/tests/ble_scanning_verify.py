import logging
import yaml
import os
from utils.test_helpers import OneshotTest
from boards.nrf52dk import Nrf52dk


class BLEScannerVerificationTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["ble_passive_scanning"])

    def test(self, board):
        # Read config file if it exists
        config_path = os.path.join(os.path.dirname(__file__), "scanner_config.yaml")
        exclude_serial = None
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = yaml.safe_load(f)
                exclude_serial = config.get("exclude_serial")

        # Create board instance with exclusion
        board = Nrf52dk(exclude_serial=exclude_serial)

        # Continue with normal test execution
        super().test(board)

    def oneshot_test(self, board):
        logging.info("Starting BLE Scanner Verification")

        # Check scanner initialization
        scan_output = board.serial.expect(
            "\\[Tutorial\\] BLE Passive Scanner", timeout=10
        )
        if not scan_output:
            raise Exception("Scanner did not initialize properly")

        # Wait for scanner to detect advertisement
        logging.info("Waiting for scanner to detect advertisement...")
        # First wait for the list header
        output = board.serial.expect("-+LIST-+", timeout=20)
        if not output:
            raise Exception("Scanner did not start printing device list")

        # Then look for specific advertiser data
        # We're looking for the device name "TockOS" in the data field
        output = board.serial.expect("TockOS", timeout=10)
        if not output:
            raise Exception("Scanner did not detect the advertiser")

        logging.info("Scanner successfully detected advertiser")


# Update the test instances
test = BLECommunicationTest()
