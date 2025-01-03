from pynrfjprog import LowLevel 
from ieee802154_tests import radio_tx_test, radio_rx_test, radio_tx_raw_test
from udp_tests import udp_send_test
from openthread_tests import openthread_hello_test

if __name__ == '__main__':
    # Scan for available devices.
    nrfjprog_api = LowLevel.API()
    nrfjprog_api.open()
    available_devices = nrfjprog_api.enum_emu_snr()
    print(available_devices)
    nrfjprog_api.close()
    radio_tx_test(available_devices)
    radio_rx_test(available_devices)
    radio_tx_raw_test(available_devices)
    #udp_send_test(available_devices)
    openthread_hello_test(available_devices)

    print("===SUCCESSFULLY PASSED ALL TESTS===")
