# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright Tock Contributors 2024.

import serial
from pexpect import fdpexpect
import logging
import queue
import re
import time
import logging


class SerialPort:
    def __init__(self, port, baudrate=115200, open_rts=None, open_dtr=None):
        self.port = port
        self.baudrate = baudrate
        self.open_rts = open_rts
        self.open_dtr = open_dtr
        self.ser = None
        self.child = None

    def open(self):
        if self.ser is None:
            try:
                self.ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=1, exclusive=True)
                self.child = fdpexpect.fdspawn(self.ser.fileno())
                if self.open_rts is not None:
                    self.ser.rts = self.open_rts
                if self.open_dtr is not None:
                    self.ser.dtr = self.open_dtr
                logging.info(f"Opened serial port {self.port} at baudrate {self.baudrate}")
            except serial.SerialException as e:
                logging.error(f"Failed to open serial port {port}: {e}")
                raise

    def is_open(self):
        return self.ser is not None
    
    def close(self):
        if self.ser is not None:
            self.ser.close()
            logging.info(f"Closed serial port {self.port}")
            self.ser = None
            self.child = None

    def set_rts(self, rts):
        assert self.ser is not None, "Serial port is not open!"
        self.ser.rts = rts

    def set_dtr(self, dtr):
        assert self.ser is not None, "Serial port is not open!"
        self.ser.dtr = dtr

    def flush_buffer(self):
        assert self.ser is not None, "Serial port is not open!"

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        logging.info("Flushed serial buffers")

    def expect(self, pattern, timeout=10, timeout_error=True):
        assert self.ser is not None, "Serial port is not open!"

        try:
            index = self.child.expect(pattern, timeout=timeout)
            return self.child.after
        except fdpexpect.TIMEOUT:
            if timeout_error:
                received_data = self.child.before.decode("utf-8", errors="replace")
                logging.error(f"Timeout waiting for pattern '{pattern}'")
                logging.error(f"Received so far:\n{received_data}")
            return None
        except fdpexpect.EOF:
            received_data = self.child.before.decode("utf-8", errors="replace")
            logging.error("EOF reached while waiting for pattern")
            logging.error(f"Received so far:\n{received_data}")
            return None

    def write(self, data):
        assert self.ser is not None, "Serial port is not open!"

        logging.debug(f"Writing data: {data}")
        for byte in data:
            self.ser.write(bytes([byte]))
            time.sleep(0.1)

class MockSerialPort:
    def __init__(self):
        self.buffer = queue.Queue()
        self.accumulated_data = b""
        self.open = False

    def open(self):
        self.open = True

    def write(self, data):
        assert self.open, "Serial port is not open!"

        logging.debug(f"Writing data: {data}")
        self.buffer.put(data)

    def expect(self, pattern, timeout=10, timeout_error=True):
        assert self.open, "Serial port is not open!"

        end_time = time.time() + timeout
        compiled_pattern = re.compile(pattern.encode())
        while time.time() < end_time:
            try:
                data = self.buffer.get(timeout=0.1)
                logging.debug(f"Received data chunk: {data}")
                self.accumulated_data += data
                if compiled_pattern.search(self.accumulated_data):
                    logging.debug(f"Matched pattern '{pattern}'")
                    return self.accumulated_data
            except queue.Empty:
                continue
        logging.error(f"Timeout waiting for pattern '{pattern}'")
        return None

    def flush_buffer(self):
        assert self.open, "Serial port is not open!"

        self.accumulated_data = b""
        while not self.buffer.empty():
            self.buffer.get()

    def close(self):
        assert self.open, "Serial port is not open!"
        self.open = False

    def reset_input_buffer(self):
        self.flush_buffer()

    def reset_output_buffer(self):
        pass
