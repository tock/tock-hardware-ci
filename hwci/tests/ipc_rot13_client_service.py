# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

from utils.test_helpers import WaitForConsoleMessageTest

test = WaitForConsoleMessageTest(
    # Apps:
    [
        "rot13_client",
        {
            "name": "rot13_service",
            "path": "rot13_service",
            "tab_file": "build/org.tockos.examples.rot13.tab",
        },
    ],
    # Expected console output:
    "12: Hello World!\n12: Uryyb Jbeyq!\n12: Hello World!\n12: Uryyb Jbeyq!\n12: Hello World!",
)
