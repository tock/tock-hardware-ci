# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
import re
from utils.test_helpers import AnalyzeConsoleTest

class CHelloAndPrintfLong(AnalyzeConsoleTest):
    def __init__(self):
        super().__init__(apps=[
            "c_hello",
            "tests/printf_long",
        ])

    def analyze(self, output):
        lines = output.decode("utf-8").split("\n")

        messages = [
            ["Hi welcome to Tock. This test makes sure that a greater than 64 byte message can be printed.", None],
            ["And a short message.", None],
            ["Hello World!", None],
        ]

        for message_idx, [message, _] in enumerate(messages):
            for line_idx, line in enumerate(lines):
                if message in line:
                    messages[message_idx][1] = line_idx
                    break

        for message, found_line in messages:
            if found_line is None:
                raise AssertionError(f"Message \"{message}\" not found in output!")

        # Ensure that the first mesage of the printf-long app arrives before its
        # second message:
        assert messages[0][1] < messages[1][1]

test = CHelloAndPrintfLong()
