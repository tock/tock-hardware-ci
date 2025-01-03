from board import Board
import sh
import time

def openthread_hello_test(boards):
    # We require 2 boards for this test.
    # TODO: Better handling/reporting of case w/o at least 2 boards.
    if len(boards) < 2:
        raise Exception("Error: [Inadequate resources] - radio_rxtx test requires at least two available boards.")
    
    # Flash the router firmware to board 0.
    sh.nrfjprog("-f", "nrf52", "--chiperase", "--program", "ot-central-controller.hex", "--reset", "--verify")

    # Create board object for libtock MTD device.
    board = Board(boards[1], 
                  "tock/boards/tutorials/nrf52840dk-thread-tutorial", 
                  "libtock-c/examples/openthread/openthread_hello", 
                  "openthread_hello", 
                  "tock/target/thumbv7em-none-eabi/release/nrf52840dk-thread-tutorial.bin")
    
    # Setup boards for test.
    board.prep_test()

    # Run test for 10 seconds and gather results.
    test_results = board.run_test(10)

    child_attach = False

    for item in test_results:
        if item == "Successfully attached to Thread network as a child.":
            child_attach = True
    
    if child_attach:
        board.log_info("PASSED: openthread_hello test")
    else:
        raise Exception("FAILED: openthread_hello test.")

