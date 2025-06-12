import logging
from core.test_harness import TestHarness


class OneshotTest(TestHarness):
    def __init__(self, apps=[]):
        self.apps = apps

    def test(self, boards):
        logging.info("Starting OneshotTest")
        if len(boards) != 1:
            raise ValueError(
                f"OneshotTest requires exactly 1 board. Got {len(boards)} boards."
            )
        single_board = boards[0]

        # Normal single-board flow:
        single_board.erase_board()
        single_board.serial.flush_buffer()
        single_board.flash_kernel()
        for app in self.apps:
            single_board.flash_app(app)

        self.oneshot_test(single_board)
        logging.info("Finished OneshotTest")

    def oneshot_test(self, board):
        pass  # To be implemented by subclasses
