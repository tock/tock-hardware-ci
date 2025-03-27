# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import argparse
import logging
import importlib.util
import sys
import os
import yaml
from pathlib import Path

#  python3 hwci/core/main.py \
#   --board-descriptors \
#     board_descriptors/fb1384d5-e1a5-469c-beb4-0d4d215c9793/board-nrf52840dk-001050202501.yml \
#     board_descriptors/fb1384d5-e1a5-469c-beb4-0d4d215c9793/board-nrf52840dk-001050244773.yml \
#   --test hwci/tests/ble_advertising_scanning_test.py


def main():
    parser = argparse.ArgumentParser(description="Run tests on Tock OS")
    parser.add_argument(
        "--board-descriptors",
        nargs="+",
        help="Paths to YAML board descriptor files (e.g. board-descriptors/.../*.yml).",
    )
    parser.add_argument("--test", required=True, help="Path to the test module")
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Ensure that Python can find 'hwci' modules
    sys.path.append(str(Path(__file__).parent.parent))

    # 1. Parse each board descriptor
    boards = []
    if not args.board_descriptors:
        logging.error(
            "No board descriptors were provided. Use --board-descriptors *.yml"
        )
        sys.exit(1)

    logging.info(f"Loading {len(args.board_descriptors)} board descriptors")
    logging.info(f"Loading test module: {args.test}")
    logging.info(f"Python path: {sys.path}")
    logging.info(f"Board descriptors: {args.board_descriptors}")

    for descriptor_path in args.board_descriptors:
        logging.info(f"Loading board descriptor: {descriptor_path}")
        with open(descriptor_path, "r") as f:
            yaml_content = f.read()
            # Log the raw YAML content
            logging.info(f"YAML content:\n{yaml_content}")
            # Parse the YAML
            board_info = yaml.safe_load(yaml_content)
        
        if not board_info:
            logging.error(f"Board descriptor file {descriptor_path} is empty or invalid.")
            sys.exit(1)

        # We expect something like: board_module: boards/nrf52dk.py
        board_module_path = board_info.get("board_module")
        if not board_module_path:
            logging.error(f"Missing 'board_module' in descriptor {descriptor_path}")
            sys.exit(1)

        # 2. Import that Python module dynamically
        if os.path.isfile(board_module_path):
            # If board_module is an actual file path (e.g. boards/nrf52dk.py)
            spec = importlib.util.spec_from_file_location(
                "board_module", board_module_path
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        else:
            # Alternatively, if it's a dotted name like "boards.nrf52dk"
            mod = importlib.import_module(board_module_path)

        # 3. Grab the 'board' object from the module
        if not hasattr(mod, "board"):
            logging.error(f"No 'board' object found in {board_module_path}")
            sys.exit(1)

        board_instance = getattr(mod, "board")

        # Optionally store descriptor metadata on the board instance
        board_instance.model = board_info.get("model")
        board_instance.serial_number = board_info.get("serial_number")
        board_instance.features = board_info.get("features", {})
        if hasattr(board_instance, "update_serial_port"):
            board_instance.update_serial_port()

        boards.append(board_instance)

    # 4. Load the test module
    test_path = args.test
    test_spec = importlib.util.spec_from_file_location("test_module", test_path)
    test_module = importlib.util.module_from_spec(test_spec)
    test_spec.loader.exec_module(test_module)

    if not hasattr(test_module, "test"):
        logging.error("No test variable found in the specified test module")
        sys.exit(1)

    test = test_module.test

    # 5. Run the test, passing our list of boards
    try:
        test.test(boards)
        logging.info("Test completed successfully!")
    except Exception as e:
        logging.exception("An error occurred during test execution")
        sys.exit(1)
    finally:
        # Cleanup each board
        for b in boards:
            b.cleanup()


if __name__ == "__main__":
    main()
