from board import Board
def radio_rxtx_test(boards):
    # We require 2 boards for this test.
    # TODO: Better handling/reporting of case w/o at least 2 boards.
    if len(boards) < 2:
        raise Exception("Error: [Inadequate resources] - radio_rxtx test requires at least two available boards.")
    
    # Create board objects for each device.
    board = Board(boards[0], 
                  "tock/boards/nordic/nrf52840dk", 
                  "libtock-c/examples/tests/ieee802154/radio_tx", 
                  "radio_tx", 
                  "tock/target/thumbv7em-none-eabi/release/nrf52840dk.bin")

    # Setup board for test.
    board.prep_test()

    # Run test for 10 seconds and gather results.
    test_tx_results = board.run_test(10)

    # The TX test transmits a packet every 250ms. For a 10s test, we expect 40 packets
    # to be succesfully transmitted. We check that 95% of packets do not fail. This
    # app prints "Transmitted succesfully" for each successful transmission.
    success_passed = 0
    TOTAL_PACKETS = 40
    for result in test_tx_results:
        if "Transmitted succesfully" in result:
            success_passed += 1
    
    # Check if 95% of packets were transmitted successfully.
    if success_passed / TOTAL_PACKETS >= 0.95:
        board.log_info("PASSED: radio_tx test")
    else:
        raise Exception("FAILED: radio_tx test -- {} out of {} packets transmitted successfully.".format(success_passed, TOTAL_PACKETS))