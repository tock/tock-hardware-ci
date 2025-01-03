# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
import re
from utils.test_helpers import OneshotTest

class SchedulerStopStartWhileoneTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["tests/whileone"])

    def oneshot_test(self, board):
        serial = board.serial

        def get_process_state():
            # Extract the process list:
            serial.write(b"list\r\n")
            process_list_re = \
                r"PID[ \t]+ShortID[ \t]+Name[ \t]+Quanta[ \t]+Syscalls[ \t]+Restarts[ \t]+Grants[ \t]+State\r\n(.*)\r\n"
            process_list_out = serial.expect(process_list_re)
            assert process_list_out is not None
            process_list_match = re.match(process_list_re, process_list_out.decode("utf-8"))

            # Extract the ID of the whileone process:
            process_list_entry_0 = process_list_match.group(1)
            assert "whileone" in process_list_entry_0

            if "Stopped(Running)" in process_list_entry_0:
                return "stopped_running"
            elif "Running" in process_list_entry_0:
                return "running"
            else:
                raise ValueError(f"Unknown process state: {process_list_entry_0}")

        # Wait for the process console to be up:
        assert serial.expect("tock") is not None

        initial_state = get_process_state()
        logging.info(f"whileone process {initial_state}")
        assert initial_state == "running"

        logging.info("Stopping whileone process")
        serial.write(b"stop whileone\r\n")
        stopped_state = get_process_state()
        logging.info(f"whileone process {stopped_state}")
        assert stopped_state == "stopped_running"

        logging.info("Starting whileone process")
        serial.write(b"start whileone\r\n")
        started_state = get_process_state()
        logging.info(f"whileone process {started_state}")
        assert started_state == "running"

test = SchedulerStopStartWhileoneTest()
