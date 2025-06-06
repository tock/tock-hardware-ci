# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import argparse
import logging
import importlib.util
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Run tests on Tock OS")
    parser.add_argument("--board", required=True, help="Path to the board module")
    parser.add_argument("--test", required=True, help="Path to the test module")
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Ensure that imported modules can find the top-level hwci modules
    # (appends the hwci root to the PYTHONPATH):
    sys.path.append(str(Path(__file__).parent.parent))

    # 1. Load board module
    board_spec = importlib.util.spec_from_file_location("board_module", args.board)
    board_module = importlib.util.module_from_spec(board_spec)
    board_spec.loader.exec_module(board_module)
    if hasattr(board_module, "board"):
        board = board_module.board
    else:
        logging.error("No board class found in the specified board module")
        sys.exit(1)

    # 5. Load test module, run test function
    test_spec = importlib.util.spec_from_file_location("test_module", args.test)
    test_module = importlib.util.module_from_spec(test_spec)
    test_spec.loader.exec_module(test_module)
    if hasattr(test_module, "test"):
        test = test_module.test
    else:
        logging.error("No test variable found in the specified test module")
        sys.exit(1)

    # Run the test
    try:
        test.test(board)
        logging.info("Test completed successfully")
    except Exception as e:
        logging.exception("An error occurred during test execution")
        sys.exit(1)
    finally:
        board.cleanup()


if __name__ == "__main__":
    main()
