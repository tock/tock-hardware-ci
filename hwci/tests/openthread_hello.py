# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2025.

"""
Test for OpenThread hello functionality.
Tests that a Tock device can join a Thread network as a child device.
"""

import time
import subprocess
import logging
import os
import tempfile
from core.test_harness import TestHarness


class OpenThreadHelloTest(TestHarness):
    # Board requirements
    BOARD_REQUIREMENTS = {
        0: {"kernel_config": "standard"},  # Router board - will be erased and flashed with Nordic firmware
        1: {"kernel_config": "thread"},  # Tock MTD board needs thread kernel
    }

    def __init__(self):
        super().__init__()

    def test(self, boards):
        # Require 2 boards for this test
        assert len(boards) >= 2, "OpenThread hello test requires at least 2 boards"

        # Board 0 will be the Thread router (flashed with Nordic firmware)
        # Board 1 will be the Tock MTD (Minimal Thread Device)
        router_board = boards[0]
        tock_board = boards[1]

        # Flash the router firmware to board 0
        # Note: This requires the ot-central-controller.hex file to be available
        print(f"Checking for Thread router firmware...")

        # First, check if router firmware file exists
        router_firmware_path = "ot-central-controller.hex"

        if os.path.exists(router_firmware_path):
            print(f"Found router firmware at {router_firmware_path}")
            try:
                # Use tockloader with OpenOCD to flash the router firmware
                # First completely erase the chip (removes any Tock kernel)
                router_board.erase_board()
                
                # Convert hex to bin for tockloader
                with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_bin:
                    # Use objcopy to convert hex to bin
                    objcopy_cmd = [
                        "arm-none-eabi-objcopy",
                        "-I", "ihex",
                        "-O", "binary",
                        router_firmware_path,
                        tmp_bin.name
                    ]
                    subprocess.run(objcopy_cmd, check=True)
                    
                    # Use tockloader to flash the binary
                    tockloader_cmd = [
                        "tockloader",
                        "flash",
                        "--openocd-serial-number", router_board.serial_number,
                        "--openocd",
                        "--openocd-board", "nordic_nrf52_dk.cfg",
                        "--address", "0x00000",
                        "--board", "nrf52dk",
                        tmp_bin.name
                    ]
                    result = subprocess.run(tockloader_cmd, capture_output=True, text=True, check=True)
                    os.unlink(tmp_bin.name)
                print(
                    f"Router firmware flashed successfully to board {router_board.serial_number}"
                )
                time.sleep(2)  # Give router time to boot
            except subprocess.CalledProcessError as e:
                print(f"Warning: Could not flash router firmware. Error: {e.stderr}")
                print("Proceeding assuming router firmware is already present")
        else:
            print(f"Warning: Router firmware {router_firmware_path} not found")
            print("IMPORTANT: This test requires a Thread router to be available")
            print("Options:")
            print("  1. Place ot-central-controller.hex in the repository root")
            print("  2. Pre-flash one board with Thread router firmware")
            print("  3. Have an external Thread router on the network")
            print("Proceeding with test...")

        # Flash Tock and the OpenThread hello app to the MTD board
        tock_board.erase_board()
        tock_board.flash_kernel()
        tock_board.flash_app("openthread/openthread_hello")

        # Wait for application to initialize
        logging.info("Waiting for OpenThread application to initialize...")
        time.sleep(2)

        # Monitor output for successful attachment
        start_time = time.time()
        test_duration = 30  # Give more time for Thread network joining
        attached = False

        logging.info(
            f"Waiting for device to join Thread network (timeout: {test_duration}s)..."
        )

        while time.time() - start_time < test_duration and not attached:
            try:
                line = tock_board.serial.expect(r".+", timeout=0.5, timeout_error=False)
                if line:
                    line_str = (
                        line.decode("utf-8", errors="replace")
                        if isinstance(line, bytes)
                        else str(line)
                    )
                    logging.debug(f"OpenThread output: {line_str.strip()}")
                    if (
                        "Successfully attached to Thread network as a child."
                        in line_str
                    ):
                        attached = True
                        logging.info("Device successfully attached to Thread network!")
                        break
            except Exception as e:
                logging.debug(f"Exception during expect: {e}")
                continue

        assert (
            attached
        ), f"OpenThread hello test failed: Device did not attach to Thread network within {test_duration} seconds"

        print(
            "OpenThread hello test passed: Device successfully attached to Thread network as a child"
        )


test = OpenThreadHelloTest()
