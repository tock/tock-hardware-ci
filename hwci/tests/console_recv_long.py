from utils.test_helpers import WaitForConsoleMessageTest

test = WaitForConsoleMessageTest(
    ["tests/console/console_recv_long"], "[SHORT] Error doing UART receive: -2"
)
