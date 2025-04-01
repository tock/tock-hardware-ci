# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import logging
import time
import subprocess
import os
from core.test_harness import TestHarness


class OpenThreadHelloTest(TestHarness):
    """
    Test for OpenThread connectivity.

    This test requires two boards:
    - Board 0: Flashed with the OpenThread border router firmware (ot-central-controller.hex)
    - Board 1: Flashed with the openthread_hello app

    The test validates:
    1. The device running openthread_hello can successfully join a Thread network
    2. The console output confirms successful attachment to the Thread network
    """

    # Configuration constants
    TEST_DURATION = 10  # seconds
    OT_ROUTER_HEX = (
        "ot-central-controller.hex"  # Path to the OpenThread router firmware
    )

    def test(self, boards):
        if len(boards) < 2:
            raise ValueError("Need at least 2 boards for OpenThread Hello test!")

        # Assign boards
        router_board = boards[0]
        client_board = boards[1]

        # Check if the OpenThread router firmware exists
        if not os.path.exists(self.OT_ROUTER_HEX):
            raise FileNotFoundError(
                f"OpenThread router firmware not found: {self.OT_ROUTER_HEX}"
            )

        # Flash the OpenThread router firmware to the first board using nrfjprog
        logging.info(
            f"Flashing OpenThread router firmware to board (SN: {getattr(router_board, 'serial_number', 'unknown')})"
        )

        # Use the board's serial number with nrfjprog if available
        router_serial = getattr(router_board, "serial_number", None)
        nrfjprog_cmd = [
            "nrfjprog",
            "-f",
            "nrf52",
            "--chiperase",
            "--program",
            self.OT_ROUTER_HEX,
            "--reset",
            "--verify",
        ]

        if router_serial:
            nrfjprog_cmd.extend(["--snr", router_serial])

        try:
            subprocess.run(nrfjprog_cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to flash OpenThread router firmware: {e}")

        # Prepare the client board
        logging.info(
            f"Preparing OpenThread client board (SN: {getattr(client_board, 'serial_number', 'unknown')})"
        )
        client_board.erase_board()
        client_board.serial.flush_buffer()
        client_board.flash_kernel()
        client_board.flash_app("openthread_hello")

        # Reset the client board to start the test
        client_board.reset()

        # Collect output from the client for TEST_DURATION seconds
        logging.info(f"Running test for {self.TEST_DURATION} seconds...")
        start_time = time.time()
        client_results = []

        while time.time() - start_time < self.TEST_DURATION:
            # Read any new line from the client console
            line = client_board.serial.expect(".+\r?\n", timeout=1, timeout_error=False)
            if line:
                text = line.decode("utf-8", errors="replace").strip()
                logging.debug(f"[OpenThread Client] {text}")
                client_results.append(text)

        # Analyze test results - look for successful Thread network attachment
        success = False
        for line in client_results:
            if line == "Successfully attached to Thread network as a child.":
                success = True
                break

        # Validate test results
        if success:
            logging.info("PASSED: OpenThread Hello test")
        else:
            error_messages = [
                "FAILED: OpenThread Hello test - Device did not attach to Thread network."
            ]

            # Provide diagnostic information from the output
            error_messages.append("\nDevice output:")
            for line in client_results:
                error_messages.append(f"  > {line}")

            raise Exception("\n".join(error_messages))


# Global test object used by the HWCI framework
test = OpenThreadHelloTest()
