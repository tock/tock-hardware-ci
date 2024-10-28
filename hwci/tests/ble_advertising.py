from utils.test_helpers import WaitForConsoleMessageTest

test = WaitForConsoleMessageTest(
    ["ble_advertising"], "Now advertising every 300 ms as 'TockOS'"
)
