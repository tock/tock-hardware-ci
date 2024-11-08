# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

from utils.test_helpers import WaitForConsoleMessageTest

# This test checks that malloc_test01 runs successfully and outputs the expected message.
test = WaitForConsoleMessageTest(["tests/malloc_test01"], "malloc01: success")
