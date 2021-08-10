from typing import Dict
import serial
from serial.serialutil import PARITY_NONE
import serial.tools.list_ports as ser_list
from serial.tools.list_ports_common import ListPortInfo
from rotary_table_api.rotary_table_messages import *

COM_PORT_VID = 0x0483
COM_PORT_PID = 0x5740
BROADCAST_ADDRESS = 0xF
CONTROLLER_ADDRESS = 0xE

def list_com_ports() -> Dict[str, ListPortInfo]:
    ports = ser_list.comports()
    ports_dict = {}
    for port in ports:
        ports_dict[port.name] = port
    return ports_dict
def is_com_port_valid(port_info: ListPortInfo) -> bool:
    """Check if COM port is USB device with correct VID and PID"""
    if isinstance(port_info, ListPortInfo):
        if port_info.pid == COM_PORT_PID and port_info.vid == COM_PORT_VID:
            return True
    return False

class RotaryTable:
    def __init__(self, port_name: str, rs_converter: bool = True):
        if rs_converter:
            self.inst = serial.Serial(port_name, baudrate=38400, parity=PARITY_NONE, timeout=1)
        else:
            self.inst = serial.Serial(port_name, timeout=1)
    
    def __del__(self):
        self.close()
    
    def send_request(self, request: Request) -> Response:
        self.inst.reset_input_buffer()
        self.inst.write(request.to_bytes())
        resp_data = self.inst.read(REPONSE_LENGTH)
        self.inst.rts = True
        if request.address == BROADCAST_ADDRESS:
            return
        if len(resp_data) == 0:
            raise IOError(f"There is no reponse from rotary table with address {request.address:d}!")
        return parse_response(resp_data)
    
    def close(self):
        self.inst.close()
