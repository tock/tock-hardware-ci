from pynrfjprog import LowLevel 
from ieee802154_tests import radio_rxtx_test

if __name__ == '__main__':
    # Scan for available devices.
    nrfjprog_api = LowLevel.API()
    nrfjprog_api.open()
    available_devices = nrfjprog_api.enum_emu_snr()
    nrfjprog_api.close()
    radio_rxtx_test(available_devices)