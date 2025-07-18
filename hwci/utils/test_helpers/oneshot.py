# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2025.

import logging
from core.test_harness import TestHarness


class OneshotTest(TestHarness):
    def __init__(self, apps=[]):
        self.apps = apps

    def test(self, boards):
        logging.info("Starting OneshotTest")
        if len(boards) == 0:
            raise ValueError("OneshotTest requires at least 1 board. Got 0 boards.")
        elif len(boards) > 1:
            logging.warning(
                f"OneshotTest expects 1 board but got {len(boards)} boards. Using only the first board."
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
