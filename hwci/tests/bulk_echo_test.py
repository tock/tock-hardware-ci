# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import logging
import os
import tempfile
import time
import random
import subprocess
import binascii
from utils.test_helpers import OneshotTest
import usb.core
import usb.util


class BulkEchoTest(OneshotTest):
    """
    Test the USB bulk endpoint echo functionality.

    This test sends data to a USB device's Bulk OUT endpoint and checks
    that the same data comes back through the Bulk IN endpoint. It's the
    Python equivalent of the tools/usb/bulk-echo Rust utility.

    The test works with the usbc_client capsule on the device which must
    be enabled by the tests/usb application.
    """

    def __init__(self):
        """Initialize the test with the usb app."""
        super().__init__(apps=["tests/usb_bulk_echo"])

        # USB device identifiers (same as in the Rust code)
        self.VENDOR_ID = 0x6667
        self.PRODUCT_ID = 0xABCD

        # Endpoints (same as in the Rust code)
        self.BULK_IN_EP = 0x81  # Endpoint 1, IN direction (0x80)
        self.BULK_OUT_EP = 0x02  # Endpoint 2, OUT direction (0x00)

        # Buffer size for transfers (same as in the Rust code: 8 bytes)
        self.BUFFER_SIZE = 8

        # Test data size
        self.TEST_DATA_SIZE = 1024

    def oneshot_test(self, board):
        """Run the bulk echo test on the provided board."""
        logging.info("Starting USB Bulk Echo Test")

        # Wait a moment for the USB application to initialize
        time.sleep(3)

        # Find our USB device
        logging.info(
            f"Looking for USB device with VID:PID {hex(self.VENDOR_ID)}:{hex(self.PRODUCT_ID)}"
        )
        dev = self._find_usb_device()

        if not dev:
            raise Exception(
                f"Could not find USB device with VID:PID {hex(self.VENDOR_ID)}:{hex(self.PRODUCT_ID)}"
            )

        logging.info(f"Found USB device: {dev}")

        # Claim the interface
        logging.info("Configuring USB device")
        try:
            # Set configuration
            dev.set_configuration()

            # Get the configuration and first interface
            cfg = dev.get_active_configuration()
            intf = cfg[(0, 0)]  # First interface, first alternate setting

            # Claim interface
            if dev.is_kernel_driver_active(0):
                logging.info("Detaching kernel driver")
                dev.detach_kernel_driver(0)

            usb.util.claim_interface(dev, 0)
            logging.info("USB interface claimed")

            # Perform the echo test
            self._run_echo_test(dev)

            # Release the interface
            usb.util.release_interface(dev, 0)

        except Exception as e:
            logging.error(f"USB test failed: {e}")
            raise

        logging.info("USB Bulk Echo Test completed successfully")

    def _find_usb_device(self):
        """Find the USB device with the specified VID and PID."""
        # Try up to 10 times with a short delay
        for _ in range(10):
            dev = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)
            if dev:
                return dev
            time.sleep(0.5)
        return None

    def _run_echo_test(self, dev):
        """
        Run the echo test by sending data to the BULK_OUT endpoint and
        verifying it comes back correctly from the BULK_IN endpoint.
        """
        # Generate random test data
        logging.info(f"Generating {self.TEST_DATA_SIZE} bytes of test data")
        test_data = bytes([random.randint(0, 255) for _ in range(self.TEST_DATA_SIZE)])

        # Create a temporary file for the test data (to mimic the original test.sh)
        with tempfile.NamedTemporaryFile(delete=False) as test_file:
            test_file_path = test_file.name
            test_file.write(test_data)

        try:
            # Send data in chunks and verify it comes back
            sent_bytes = 0
            received_bytes = 0
            received_data = bytearray()

            logging.info(f"Starting to send {len(test_data)} bytes of data")

            # Send all the data
            while sent_bytes < len(test_data):
                # Get next chunk to send
                chunk_size = min(self.BUFFER_SIZE, len(test_data) - sent_bytes)
                chunk = test_data[sent_bytes : sent_bytes + chunk_size]

                # Send the chunk
                bytes_written = dev.write(self.BULK_OUT_EP, chunk, timeout=1000)
                if bytes_written != len(chunk):
                    raise Exception(
                        f"Short write: wrote {bytes_written} bytes instead of {len(chunk)}"
                    )

                sent_bytes += bytes_written
                logging.debug(
                    f"Sent {bytes_written} bytes, total {sent_bytes}/{len(test_data)}"
                )

                # Try to read data back (non-blocking)
                while received_bytes < sent_bytes:
                    try:
                        data = dev.read(self.BULK_IN_EP, self.BUFFER_SIZE, timeout=3000)
                        if data:
                            received_data.extend(data)
                            received_bytes += len(data)
                            logging.debug(
                                f"Received {len(data)} bytes, total {received_bytes}/{sent_bytes}"
                            )
                    except usb.core.USBError as e:
                        if e.errno == 110:  # Operation timed out
                            logging.debug("Read timeout, continuing")
                            break
                        else:
                            raise

            # Continue reading until we've received all sent bytes
            timeout_count = 0
            max_timeouts = 10  # Allow up to 10 consecutive timeouts

            while received_bytes < sent_bytes and timeout_count < max_timeouts:
                try:
                    data = dev.read(self.BULK_IN_EP, self.BUFFER_SIZE, timeout=3000)
                    if data:
                        received_data.extend(data)
                        received_bytes += len(data)
                        timeout_count = 0  # Reset timeout counter on successful read
                        logging.debug(
                            f"Received {len(data)} bytes, total {received_bytes}/{sent_bytes}"
                        )
                except usb.core.USBError as e:
                    if e.errno == 110:  # Operation timed out
                        timeout_count += 1
                        logging.debug(
                            f"Read timeout ({timeout_count}/{max_timeouts}), continuing"
                        )
                    else:
                        raise

            # Check if we received everything
            if received_bytes < sent_bytes:
                raise Exception(
                    f"Did not receive all data. Sent: {sent_bytes}, Received: {received_bytes}"
                )

            # Verify data matches
            if test_data != received_data:
                # Find the first mismatch for better error reporting
                mismatch_idx = None
                for i in range(min(len(test_data), len(received_data))):
                    if test_data[i] != received_data[i]:
                        mismatch_idx = i
                        break

                if mismatch_idx is not None:
                    context_start = max(0, mismatch_idx - 8)
                    context_end = min(len(test_data), mismatch_idx + 8)
                    sent_context = binascii.hexlify(
                        test_data[context_start:context_end]
                    ).decode()
                    received_context = binascii.hexlify(
                        received_data[context_start:context_end]
                    ).decode()

                    raise Exception(
                        f"Data mismatch at byte {mismatch_idx}.\n"
                        f"Sent [{context_start}:{context_end}]: {sent_context}\n"
                        f"Recv [{context_start}:{context_end}]: {received_context}"
                    )
                else:
                    raise Exception(
                        "Data length mismatch, but content matched up to the shorter length"
                    )

            logging.info(f"Successfully echoed {received_bytes} bytes")

        finally:
            # Clean up the temporary file
            if os.path.exists(test_file_path):
                os.unlink(test_file_path)


# Create the test instance
test = BulkEchoTest()
