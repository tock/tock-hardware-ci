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

    # Load test module early to get board requirements if any
    test_module = None
    test_requirements = {}
    try:
        test_path = args.test
        test_spec = importlib.util.spec_from_file_location("test_module", test_path)
        test_module = importlib.util.module_from_spec(test_spec)
        test_spec.loader.exec_module(test_module)
        
        # Look for test requirements
        if hasattr(test_module, "test"):
            test_instance = test_module.test
            test_class = test_instance.__class__
            if hasattr(test_class, "BOARD_REQUIREMENTS"):
                test_requirements = test_class.BOARD_REQUIREMENTS
                logging.info(f"Found test board requirements: {test_requirements}")
    except Exception as e:
        logging.debug(f"Could not load test requirements: {e}")
        # Will load test module again later

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

    for board_index, descriptor_path in enumerate(args.board_descriptors):
        logging.info(f"Loading board descriptor: {descriptor_path}")
        with open(descriptor_path, "r") as f:
            yaml_content = f.read()
            # Log the raw YAML content
            logging.info(f"YAML content:\n{yaml_content}")
            # Parse the YAML
            board_info = yaml.safe_load(yaml_content)
            
        if not board_info:
            logging.error(
                f"Board descriptor file {descriptor_path} is empty or invalid."
            )
            sys.exit(1)

        # We expect something like: board_module: boards/nrf52dk.py
        board_module_path = board_info.get("board_module")
        
        # Merge test requirements for this board index if any
        if board_index in test_requirements:
            requirements = test_requirements[board_index]
            logging.info(f"Applying test requirements for board {board_index}: {requirements}")
            # Test requirements override descriptor values
            board_info.update(requirements)
            # If test specifies a different board module, use it
            if "board_module" in requirements:
                board_module_path = requirements["board_module"]
                logging.info(f"Test overrides board module to: {board_module_path}")
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

        # 3. Create board instance using factory function or grab existing board
        if hasattr(mod, "create_board"):
            # Use factory function with all board descriptor data (including test requirements)
            board_instance = mod.create_board(**board_info)
        elif hasattr(mod, "board"):
            # Fallback to old style - grab pre-created board object
            board_instance = getattr(mod, "board")
            # Store all descriptor metadata (including test requirements) on the board instance
            for key, value in board_info.items():
                setattr(board_instance, key, value)
            if hasattr(board_instance, "update_serial_port"):
                board_instance.update_serial_port()
        else:
            logging.error(f"No 'create_board' function or 'board' object found in {board_module_path}")
            sys.exit(1)

        boards.append(board_instance)

    # 4. Load the test module (if not already loaded for requirements)
    if test_module is None:
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
