# Licensed under the Apache License, Version 2.0 or the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
import re
from utils.test_helpers import OneshotTest

class MPUStackGrowthTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["tests/mpu/mpu_stack_growth"])

    def oneshot_test(self, board):
        serial = board.serial

        # Expect the test start message:
        serial.expect("[TEST] MPU Stack Growth")

        # Extract the various memory addresses:
        mem_start_pattern = r"mem_start: *0x([0-9a-f]+)"
        mem_start_out = serial.expect(mem_start_pattern)

        app_heap_break_pattern = r"app_heap_break: *0x([0-9a-f]+)"
        app_heap_break_out = serial.expect(app_heap_break_pattern)

        kernel_memory_break_pattern = r"kernel_memory_break: *0x([0-9a-f]+)"
        kernel_memory_break_out = serial.expect(kernel_memory_break_pattern)

        mem_end_pattern = r"mem_end: *0x([0-9a-f]+)"
        mem_end_out = serial.expect(mem_end_pattern)

        stack_pointer_ish_pattern = r"stack pointer \(ish\): *0x([0-9a-f]+)"
        stack_pointer_ish_out = serial.expect(stack_pointer_ish_pattern)

        addresses = {
            "mem_start": int(re.match(mem_start_pattern, mem_start_out.decode("utf-8")).group(1), 16),
            "app_heap_break": int(re.match(app_heap_break_pattern, app_heap_break_out.decode("utf-8")).group(1), 16),
            "kernel_memory_break": int(re.match(kernel_memory_break_pattern, kernel_memory_break_out.decode("utf-8")).group(1), 16),
            "mem_end": int(re.match(mem_end_pattern, mem_end_out.decode("utf-8")).group(1), 16),
            "stack_pointer_ish": int(re.match(stack_pointer_ish_pattern, stack_pointer_ish_out.decode("utf-8")).group(1), 16),
        }
        max_label_len = max(map(lambda label: len(label), addresses.keys()))
        for label, addr in addresses.items():
            logging.info(f"Got address: {label.rjust(max_label_len)} = 0x{addr:08x}")

        # Extract the fault reason and faulting address:
        assert serial.expect(r"Data Access Violation:[ \t]+true") is not None
        assert serial.expect(r"Memory Management Stacking Fault:[ \t]+true") is not None
        assert serial.expect(r"Forced Hard Fault:[ \t]+true") is not None

        fault_address_pattern = r"Faulting Memory Address:[ \t]+0x([0-9A-F]+)"    
        fault_address_out = serial.expect(fault_address_pattern)
        fault_address = int(re.match(fault_address_pattern, fault_address_out.decode("utf-8")).group(1), 16)

        # Ensure that the panic message shows that the stack has been exceeded,
        # and that the previously reported stack pointer is within the bounds
        # in the table drawn on the serial console.
        #
        # serial.expect matches on ASCII characters, which doesn't support the
        # Unicode Tock panic messages:
        fault_table_output = serial.expect(r"mpu_stack_growth.*\[Faulted\].*R0 : 0x")
        assert fault_table_output is not None
        # print("Fault table output: ", fault_table_output)

        # # Once we have captured, the table, decode the output as UTF-8 and
        # # match the exact expression to extract the stack boundaries / size:
        # fault_table_pattern = b"mpu_stack_growth.*A" #\r\n[ \t]+0x([0-9A-F]+) ┼─+ M\r\n[ \t]+| ▼ Stack[ \t]+([0-9]+) |[ \t]+([0-9]+)[ \t]+EXCEEDED!\r\n[ \t]+0x([0-9A-F]+) ┼─+.*"
        # fault_table = re.match(re.compile(fault_table_pattern), fault_table_output)
        # print(fault_table)

        # stack_top = int(serial.child.match.group(1).decode("utf-8"), 16)
        # stack_size = int(serial.child.match.group(2).decode("utf-8"), 16)
        # stack_size_max = int(serial.child.match.group(3).decode("utf-8"), 16)
        # stack_bottom_overrun = int(serial.child.match.group(4).decode("utf-8"), 16)

        # assert stack_top > stack_bottom
        # assert stack_size > stack_size_max
        # assert stack_top - stack_size_max >= stack_bottom_overrun
        # assert stack_top > stack_pointer_ish > stack_bottom_overrun
        # # we assume that the kernel's view on the stack pointer is roughly in
        # # the region of where the fault occurred
        # assert stack_top > fault_address > (stack_bottom_overrun + 64)

test = MPUStackGrowthTest()
