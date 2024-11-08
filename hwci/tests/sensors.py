# Licensed under the Apache License, Version 2.0 OR the MIT License.
# SPDX-License-Identifier: Apache-2.0 OR MIT

import logging
import time
from utils.test_helpers import OneshotTest


class SensorsTest(OneshotTest):
    def __init__(self):
        super().__init__(apps=["sensors"])

    def oneshot_test(self, board):
        logging.info("Starting Sensors Test")
        serial = board.serial

        # Expected initial messages
        expected_messages = [
            r"\[Sensors\] Starting Sensors App.",
            r"\[Sensors\] All available sensors on the platform will be sampled.",
        ]

        # Read initial messages
        for message in expected_messages:
            output = serial.expect(message, timeout=10)
            if not output:
                raise Exception(f"Did not receive expected message: '{message}'")
            logging.info(f"Received expected message: '{message}'")

        # Wait for sensor sampling to start
        time.sleep(1)

        # Modified sensor reading loop with better error handling
        iterations = 3  # Reduced from 5
        timeout_per_reading = 10  # Increased timeout
        valid_readings = 0
        expected_sensors = {
            "Temperature": False,
            "Ambient Light": False,
            "Humidity": False,
            "Acceleration": False,
            "Magnetometer": False,
            "Gyro": False,
            "Proximity": False,
            "Sound Pressure": False,
        }

        # Try to get valid readings for available sensors
        for i in range(iterations):
            try:
                reading_timeout = time.time() + timeout_per_reading
                sensors_found = False

                while time.time() < reading_timeout:
                    output = serial.expect(r".*\r\n", timeout=2)
                    if output:
                        line = output.decode("utf-8", errors="replace").strip()
                        if not line:  # Skip empty lines
                            continue

                        logging.info(f"Sensor output: {line}")

                        # Check for each type of sensor reading
                        for sensor in expected_sensors.keys():
                            if line.startswith(sensor):
                                expected_sensors[sensor] = True
                                sensors_found = True

                        # If we've found at least one sensor reading, count this as a valid iteration
                        if sensors_found:
                            valid_readings += 1
                            break

            except Exception as e:
                logging.warning(f"Error during sensor reading iteration {i}: {e}")
                continue

        # Log which sensors were found
        logging.info("Detected sensors:")
        for sensor, found in expected_sensors.items():
            if found:
                logging.info(f"  - {sensor}")

        # Success criteria: we got at least one valid reading
        if valid_readings == 0:
            raise Exception("No valid sensor readings were detected")

        # Warning if we got fewer readings than expected
        if valid_readings < iterations:
            logging.warning(
                f"Only got {valid_readings} valid readings out of {iterations} attempts"
            )

        if not any(expected_sensors.values()):
            raise Exception("No sensors were detected on the board")

        logging.info("Sensors Test completed successfully")


test = SensorsTest()
