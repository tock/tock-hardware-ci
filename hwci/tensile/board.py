from pynrfjprog import LowLevel
import coloredlogs, logging
import sh
import serial, time

BAUD_RATE = 115200

class Board:
    def __init__(self, board_serial_no, kernel_path, libtock_path, app_name, binary_path):
        self.board_serial_no = board_serial_no
        self.board_com_port = None
        self.nrfjprog_api = None
        self.kernel_path = kernel_path
        self.libtock_path = libtock_path
        self.app_name = app_name
        self.binary_path = binary_path  
        
        # Create and configure logging object for this board.
        self.logger = logging.getLogger(__name__)
        coloredlogs.install(level='INFO', logger=self.logger, fmt='%(message)s')

    def log_info(self, msg):
        self.logger.info(msg)


    def init_nrfjprog(self):
        # Init/open API.
        nrfjprog_api = LowLevel.API()
        nrfjprog_api.open()
        
        # Connect to board with serial number.
        nrfjprog_api.connect_to_emu_with_snr(self.board_serial_no)

        self.nrfjprog_api = nrfjprog_api
        # Get COM port for this board. NOTE: Newer nordic devices
        # occasionally have 2 COM ports. We select the lower port.
        board_com_port = nrfjprog_api.enum_emu_com_ports(self.board_serial_no)
        if len(board_com_port) > 1:
            self.board_com_port = board_com_port[0].path

    def flash_board(self):
        # Reset board to factory settings and erase all flash.
        self.log_info(f"[FACTORY_RESET] Beginning factory reset for board {self.board_serial_no}...")
        self.nrfjprog_api.recover()

        self.log_info(f"[FACTORY_RESET -- COMPLETE] {self.board_serial_no}.")
        
        # Build Tock kernel.
        self.log_info(f"[BUILDING] Tock Kernel {self.kernel_path}...")
        self.log_info(sh.make("-C", self.kernel_path, _err_to_out=True))
        self.log_info(f"[BUILDING -- COMPLETE] Tock Kernel {self.kernel_path}.")
        
        # Flash Tock kernel to board.
        self.log_info(f"[FLASHING] Tock Kernel to: {self.board_serial_no}...")
        self.log_info(sh.tockloader(
                        "flash", 
                        "--address", 
                        "0x00000", 
                        "--board", 
                        "nrf52dk", 
                        "--jlink-serial-number", 
                        self.board_serial_no,
                        "--jlink",
                        self.binary_path, 
                        _err_to_out=True))

        self.log_info(f"[FLASHING -- COMPLETE] {self.board_serial_no}.") 

        # Build libtock-c app.
        self.log_info(f"[BUILDING] libtock-c app {self.app_name}...")
        self.log_info(sh.make("-C", self.libtock_path, _err_to_out=True))
        self.log_info(f"[BUILDING -- COMPLETE] {self.app_name}.")

        # Flash libtock-c app to board.
        self.log_info(f"[FLASHING] libtock-c app {self.app_name} to: {self.board_serial_no}...")
        self.log_info(sh.tockloader(
                        "install", 
                        f"{self.libtock_path}/build/{self.app_name}.tab",
                        "--jlink-serial-number", 
                        self.board_serial_no, 
                        _err_to_out=True))
        self.log_info(f"[FLASHING -- COMPLETE] {self.app_name}.")


    def panic_board(self):
        ser = serial.Serial(self.board_com_port, BAUD_RATE)
        encode_and_send("panic", ser)
        ser.close()
    
    def prep_test(self):
        self.init_nrfjprog()
        self.flash_board()

        self.panic_board()
        self.log_info(f"[READY] {self.board_serial_no} initialized and halted.")
        self.nrfjprog_api.close()

    # Function to run test. Output_queue is used to place output (instead of return)
    def run_test(self, duration):
        self.init_nrfjprog()
        # We reset board and save output to log
        ser = serial.Serial(self.board_com_port, BAUD_RATE, timeout = 1)

        input = []

        self.log_info(f"[RUNNING] {self.app_name} test on {self.board_serial_no} for {duration} seconds...")
        self.nrfjprog_api.debug_reset()
        self.nrfjprog_api.close()
        
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                input.append(ser.readline().decode('ascii').strip())
            except: 
                continue

        ser.close()
        self.nrfjprog_api.close()

        self.log_info(f"[COMPLETE] {self.app_name} test on {self.board_serial_no}.")
        return input 

def encode_and_send(input_str, ser):
    input_str += "\r\n"
    input_str = input_str.replace('\\r', '\r').replace('\\n', '\n')
    encoded_data = input_str.encode('ascii')
    ser.write(encoded_data)
