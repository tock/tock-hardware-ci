import logging
from core.test_harness import TestHarness


class OneshotTest(TestHarness):
    def __init__(self, apps=[]):
        self.apps = apps

    def test(self, board):
        logging.info("Starting OneshotTest")
        board.erase_board()

        # For some boards, we need to open the serial console during flash to
        # capture the initial messages:
        if board.open_serial_during_flash:
            board.serial.open()

        board.flash_kernel()
        for app in self.apps:
            board.flash_app(app)

        # For other boards (such as Imix), we can only open the serial after
        # the board has been flashed:
        if not board.open_serial_during_flash:
            board.serial.open()

        self.oneshot_test(board)

        logging.info("Finished OneshotTest")
        board.serial.close()

    def oneshot_test(self, board):
        pass  # To be implemented by subclasses
