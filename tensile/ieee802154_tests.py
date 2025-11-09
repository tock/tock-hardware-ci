from board import Board

def radio_rx_test(boards, test_duration_sec=10):
    # We require 2 boards for this test.
    # TODO: Better handling/reporting of case w/o at least 2 boards.
    if len(boards) < 2:
        raise Exception("Error: [Inadequate resources] - radio_rxtx test requires at least two available boards.")
    
    # Create board objects for tx device.
    board_tx = Board(boards[0], 
                  "tock/boards/nordic/nrf52840dk", 
                  "libtock-c/examples/tests/ieee802154/radio_tx", 
                  "radio_tx", 
                  "tock/target/thumbv7em-none-eabi/release/nrf52840dk.bin")
    
    # Create board object for rx device.
    board_rx = Board(boards[2], 
                  "tock/boards/nordic/nrf52840dk", 
                  "libtock-c/examples/tests/ieee802154/radio_rx", 
                  "radio_rx", 
                  "tock/target/thumbv7em-none-eabi/release/nrf52840dk.bin")

    # Setup boards for test.
    board_tx.prep_test()
    board_rx.prep_test()

    # Run tests.
    board_tx.run_test(1)
    test_rx_results = board_rx.run_test(test_duration_sec)

    # The standard TX test transmits a packet every 250ms. 
    success_passed = 0
    TOTAL_PACKETS = test_duration_sec * 4

    index = 0
    while index < len(test_rx_results):
        if index + 8 < len(test_rx_results) \
                and "Received packet with payload of 60 bytes from offset 12" in test_rx_results[index] \
                and "00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f" in test_rx_results[index+1] \
                and "10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f" in test_rx_results[index+2] \
                and "20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f" in test_rx_results[index+3] \
                and "30 31 32 33 34 35 36 37 38 39 3a 3b" in test_rx_results[index+4] \
                and "Packet destination PAN ID: 0xabcd" in test_rx_results[index+5] \
                and "Packet destination address: 0x0802" in test_rx_results[index+6] \
                and "Packet source PAN ID: 0xabcd" in test_rx_results[index+7] \
                and "Packet source address: 0x1540" in test_rx_results[index+8]:
                    success_passed += 1
                    index += 9
        else:
            index += 1

            

    # Check if 50% of packets were transmitted successfully.
    if success_passed / TOTAL_PACKETS >= 0.50:
        board_rx.log_info("PASSED: radio_rx test")
    else:
        raise Exception("FAILED: radio_rx test -- {} out of {} packets transmitted successfully. \
                        Dump of received packets:\n {}".format(success_passed, TOTAL_PACKETS, test_rx_results))

def radio_tx_raw_test(boards, test_duration_sec=10):
    # We require 2 boards for this test.
    # TODO: Better handling/reporting of case w/o at least 2 boards.
    if len(boards) < 2:
        raise Exception("Error: [Inadequate resources] - radio_rxtx test requires at least two available boards.")
    
    # Create board objects for tx device.
    board_tx = Board(boards[0], 
                  "tock/boards/tutorials/nrf52840dk-thread-tutorial", 
                  "libtock-c/examples/tests/ieee802154/radio_tx_raw", 
                  "radio_tx_raw", 
                  "tock/target/thumbv7em-none-eabi/release/nrf52840dk-thread-tutorial.bin")
    
    # Create board object for rx device.
    board_rx = Board(boards[2], 
                  "tock/boards/nordic/nrf52840dk", 
                  "libtock-c/examples/tests/ieee802154/radio_rx", 
                  "radio_rx", 
                  "tock/target/thumbv7em-none-eabi/release/nrf52840dk.bin")

    # Setup boards for test.
    board_tx.prep_test()
    board_rx.prep_test()

    # Run test.
    board_tx.run_test(1)
    test_rx_results = board_rx.run_test(test_duration_sec)

    # The TX_RAW test transmits a packet every 500ms.
    success_passed = 0
    TOTAL_PACKETS = 2 * test_duration_sec 

    index = 0

    while index < len(test_rx_results):
        if index + 8 < len(test_rx_results) \
                and "Received packet with payload of 60 bytes from offset 18" in test_rx_results[index] \
                and "00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f" in test_rx_results[index+1] \
                and "10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f" in test_rx_results[index+2] \
                and "20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f" in test_rx_results[index+3] \
                and "30 31 32 33 34 35 36 37 38 39 3a 3b" in test_rx_results[index+4] \
                and "Packet destination PAN ID: 0xabcd" in test_rx_results[index+5] \
                and "Packet destination address: 0xffff" in test_rx_results[index+6] \
                and "Packet source PAN ID: 0xabcd" in test_rx_results[index+7] \
                and "Packet source address: 00 00 00 00 00 00 00 00" in test_rx_results[index+8]:
                    success_passed += 1
                    index += 9
        else:
            index += 1

    # Check if 50% of packets were transmitted successfully.
    if success_passed / TOTAL_PACKETS >= 0.50:
        board_rx.log_info("PASSED: radio_tx_raw test")
    else:
        raise Exception("FAILED: radio_tx_raw test -- {} out of {} packets transmitted successfully. Dump of \
                received packets: \n {}".format(success_passed, TOTAL_PACKETS, test_rx_results))

def radio_tx_test(boards, test_duration_sec=10):
    # Create board objects for each device.
    board = Board(boards[0], 
                  "tock/boards/nordic/nrf52840dk", 
                  "libtock-c/examples/tests/ieee802154/radio_tx", 
                  "radio_tx", 
                  "tock/target/thumbv7em-none-eabi/release/nrf52840dk.bin")

    # Setup board for test.
    board.prep_test()

    # Run test.
    test_tx_results = board.run_test(test_duration_sec)

    # The TX test transmits a packet every 250ms. 
    success_passed = 0
    TOTAL_PACKETS = test_duration_sec * 4

    for result in test_tx_results:
        if "Transmitted successfully." in result:
            success_passed += 1
    
    # Check if 95% of packets were transmitted successfully.
    if success_passed / TOTAL_PACKETS >= 0.95:
        board.log_info("PASSED: radio_tx test")
    else:
        raise Exception("FAILED: radio_tx test -- {} out of {} packets transmitted successfully.".format(success_passed, TOTAL_PACKETS))
