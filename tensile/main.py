from pynrfjprog import LowLevel 
from ieee802154_tests import libtock_c_radio_rx_test, libtock_c_radio_tx_raw_test, libtock_c_radio_tx_test, libtock_rs_radio_raw_test
from openthread_tests import openthread_hello_test

if __name__ == '__main__':
    # Scan for available devices.
    nrfjprog_api = LowLevel.API()
    nrfjprog_api.open()
    available_devices = nrfjprog_api.enum_emu_snr()
    print(available_devices)
    nrfjprog_api.close()

    # libtock-c tests #
    libtock_c_radio_tx_test(available_devices)
    libtock_c_radio_rx_test(available_devices, 60)
    libtock_c_radio_tx_raw_test(available_devices, 60)
    openthread_hello_test(available_devices)

    # libtock-rs tests #
    libtock_rs_radio_raw_test(available_devices, 60)

    print("===SUCCESSFULLY PASSED ALL TESTS===")
