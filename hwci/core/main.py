# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import argparse
import logging
import importlib.util
import sys


def main():
    parser = argparse.ArgumentParser(description="Run tests on Tock OS")
    # Instead of a single board, we now allow multiple boards
    parser.add_argument(
        "--boards",
        nargs="+",
        required=True,
        help="Paths to the board modules (one per board)",
    )
    # We still allow a single test module as before
    parser.add_argument("--test", required=True, help="Path to the test module")
    # New argument: multiple apps, one corresponding to each board
    parser.add_argument(
        "--apps", nargs="+", help="List of apps to flash, one per board"
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Load the test module once
    test_spec = importlib.util.spec_from_file_location("test_module", args.test)
    test_module = importlib.util.module_from_spec(test_spec)
    test_spec.loader.exec_module(test_module)
    if not hasattr(test_module, "test"):
        logging.error("No test variable found in the specified test module")
        sys.exit(1)
    test = test_module.test

    # Check if the number of apps matches the number of boards (if provided)
    if args.apps and len(args.apps) != len(args.boards):
        logging.error("Number of apps must match the number of boards")
        sys.exit(1)

    # If apps are not provided, we assume no apps need to be flashed or
    # rely on defaults (this depends on your setup)
    apps = args.apps if args.apps else [None] * len(args.boards)

    # Iterate over each board, load it, flash kernel/app, and run the test
    for i, board_path in enumerate(args.boards):
        board_spec = importlib.util.spec_from_file_location("board_module", board_path)
        board_module = importlib.util.module_from_spec(board_spec)
        board_spec.loader.exec_module(board_module)
        if not hasattr(board_module, "board"):
            logging.error("No board class found in the specified board module")
            sys.exit(1)

        board = board_module.board

        # Prepare the board: erase, flash kernel, flash app if specified
        try:
            board.erase_board()
            board.serial.flush_buffer()
            board.flash_kernel()

            if apps[i]:
                # Flash the specified app for this board
                board.flash_app(apps[i])

            # Run the test on this board
            test.test(board)
            logging.info(f"Test completed successfully on board {board_path}")
        except Exception as e:
            logging.exception(
                f"An error occurred during test execution on board {board_path}"
            )
            sys.exit(1)
        finally:
            board.cleanup()


if __name__ == "__main__":
    main()
