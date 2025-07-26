# OpenThread Test Requirements

## Router Firmware

The OpenThread hello test requires a Thread router firmware to be flashed to one of the boards. This test expects the `ot-central-controller.hex` file to be available in the working directory.

### Options for the Router Firmware:

1. **Pre-flashed Router**: If one of the boards already has Thread router firmware, the test will proceed even if the hex file is not found.

2. **Provide the Hex File**: Place the `ot-central-controller.hex` file in the root directory of the repository before running the test.

3. **Alternative Router Setup**: You can modify the test to use a different router firmware or skip the router flashing step if you have a Thread router already running on the network.

### Obtaining the Router Firmware

The `ot-central-controller.hex` file is typically a Nordic SDK example or OpenThread Border Router firmware compiled for the nRF52840. You can:

- Build it from the Nordic SDK examples
- Use a pre-built OpenThread Border Router image
- Use any Thread router firmware compatible with nRF52840

The test will warn but continue if the hex file is not found, assuming a router is already available.
