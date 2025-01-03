# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
import re
from utils.test_helpers import OneshotTest

class SchedulerRestartWhileoneTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["tests/whileone"])

    def oneshot_test(self, board):
        serial = board.serial

        def get_process_id():
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
            process_list_entry_0_match = re.match(r"[ \t]*([0-9]+)[ \t]+", process_list_entry_0)
            whileone_pid = int(process_list_entry_0_match.group(1))
            return whileone_pid

        # Wait for the process console to be up:
        assert serial.expect("tock") is not None

        initial_pid = get_process_id()
        logging.info(f"whileone process running with PID {initial_pid}")

        logging.info("Restarting whileone process")
        serial.write(b"terminate whileone\r\n")
        time.sleep(0.5)
        serial.write(b"boot whileone\r\n")

        new_pid = get_process_id()
        logging.info(f"whileone process running with PID {new_pid}")
        assert new_pid > initial_pid

test = SchedulerRestartWhileoneTest()
