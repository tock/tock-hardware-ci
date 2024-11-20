# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

#!/usr/bin/env python3

import os
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Select all HWCI tests.")
    parser.add_argument(
        "--repo-path",
        type=str,
        default=".",
        help="Path to the tock/tock repository to analyze",
    )
    parser.add_argument(
        "--hwci-path",
        type=str,
        required=True,
        help="Path to the tock-hardware-ci repository",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="selected_tests.json",
        help="Output JSON file for selected tests",
    )
    args = parser.parse_args()

    # For now, we ignore the repo-path (tock/tock repository) since we are not analyzing changes yet
    # In the future, we will use repo-path to analyze the changes and select tests accordingly

    # Path to the tests directory within the tock-hardware-ci repository
    tests_dir = os.path.join(args.hwci_path, "tests")

    # Find all .py files in the tests directory
    test_files = []
    for root, dirs, files in os.walk(tests_dir):
        for file in files:
            if file.endswith(".py"):
                # Get the relative path to the test file
                test_path = os.path.relpath(os.path.join(root, file), args.hwci_path)
                test_files.append(test_path)

    # Output the list of test files as a JSON array
    with open(args.output, "w") as f:
        json.dump(test_files, f)

    print(f"Selected HWCI tests: {test_files}")

if __name__ == "__main__":
    main()
