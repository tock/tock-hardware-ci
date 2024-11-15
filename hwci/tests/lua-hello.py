# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import logging
import os
import subprocess
from utils.test_helpers import WaitForConsoleMessageTest
from utils.test_helpers import OneshotTest


class LuaHelloTest(WaitForConsoleMessageTest):
    def __init__(self):
        super().__init__(["lua-hello"], "Hello from Lua!")

    def test(self, board):
        # Initialize and update Lua submodule before running the test
        libtock_c_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "libtock-c",
        )
        lua_dir = os.path.join(libtock_c_dir, "examples", "lua-hello")

        try:
            # Initialize the Lua submodule
            logging.info("Initializing Lua submodule...")
            subprocess.run(
                ["git", "submodule", "init", "--", "lua"], cwd=lua_dir, check=True
            )

            # Update the Lua submodule
            logging.info("Updating Lua submodule...")
            subprocess.run(["git", "submodule", "update"], cwd=lua_dir, check=True)

            # Run the parent class's test method
            super().test(board)

        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to initialize/update Lua submodule: {e}")
            raise
        except Exception as e:
            logging.error(f"Error during test execution: {e}")
            raise


test = LuaHelloTest()
