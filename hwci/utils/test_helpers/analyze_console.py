import logging
from utils.test_helpers import OneshotTest

class AnalyzeConsoleTest(OneshotTest):
    def oneshot_test(self, board):
        logging.info("Starting AnalyzeConsoleTest")
        collected_output = b""
        serial = board.serial
        try:
            while True:
                output = serial.expect(".+", timeout=5, timeout_error=False)
                if output is not None:
                    line = output.decode("utf-8", errors="replace").strip()
                    logging.info(f"SERIAL OUTPUT: {line}")
                    collected_output += output
                else:
                    break
        except Exception as e:
            logging.error(f"Error during serial communication: {e}")

        self.analyze(collected_output)
        logging.info("Finished AnalyzeConsoleTest")

    def analyze(self, output):
        pass  # To be implemented by subclasses
