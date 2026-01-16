# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2025.

import logging
from utils.test_helpers import OneshotTest

class AnalyzeConsoleTest(OneshotTest):
    def oneshot_test(self, board):
        logging.info("Starting AnalyzeConsoleTest")
        collected_output = b""
        serial = board.serial
        try:
            while True:
                output = serial.expect(".+", timeout=5, timeout_error=False)
                if output is not None:
                    collected_output += output
                else:
                    break
        except Exception as e:
            logging.error(f"Error during serial communication: {e}")

        logging.info(f"Captured output: {collected_output.decode('utf-8', errors='replace')}")
        self.analyze(collected_output)
        logging.info("Finished AnalyzeConsoleTest")

    def analyze(self, output):
        pass  # To be implemented by subclasses
