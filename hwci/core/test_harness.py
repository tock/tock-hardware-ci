# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.


class TestHarness(object):
    """Base class for all tests. By default it does nothing with the boards."""

    def test(self, boards):
        """Entry point: a list of BoardHarness objects is passed."""
        pass
