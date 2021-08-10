from typing import List, NoReturn, Tuple, Dict

from numpy.core.fromnumeric import trace
from pyvisa.constants import VI_ERROR_TMO
from vna_anritsu_MS20xxC_api.vna_types import *

import pyvisa
import re
import skrf as rf
import numpy as np
import time

TRACES_MAPPING = {
    1: SParam.S11,
    2: SParam.S12,
    3: SParam.S21,
    4: SParam.S22
}
EXCEPTION_PREFIX = "VNA_COMMUNICATION: "

def list_visa_instruments(rm: pyvisa.ResourceManager) -> Tuple[str, ...]:
    return rm.list_resources()
def find_vna_instrument_by_idn(rm: pyvisa.ResourceManager) -> str:
    instruments = list_visa_instruments(rm)
    for inst_name in instruments:
        if is_instrument_supported(get_instrument_idn(rm, inst_name)):
            return inst_name
    return None
def get_instrument_idn(resource_manager: pyvisa.ResourceManager, inst_name: str) -> str:
    inst = resource_manager.open_resource(inst_name)
    try:
        idn = inst.query("*IDN?")
    except pyvisa.VisaIOError as err:
        return None
    finally:
        inst.close()
    return idn

def is_instrument_supported(identification) -> bool:
    if identification is None:
        return False
    idn = identification[1:-1].split(",")
    pat = re.compile("^MS20[0-9]{2}C")
    return len(idn) > 1 and idn[0] == "Anritsu" and pat.match(idn[1]) is not None
def convert_traces_data_to_s2p(traces_data: Dict[str, np.ndarray], freq_data: np.ndarray) -> rf.Network:
    s2p = np.empty(shape=(len(freq_data),2,2), dtype=np.complex128)
    for data in traces_data.values():
        if len(data) != len(freq_data):
            raise ValueError("Unable to create s2p matrix from traces_data. Lengths of trace_data and freq_data are different.")
    
    s2p[:, 0, 0] = traces_data[SParam.S11]
    s2p[:, 0, 1] = traces_data[SParam.S12]
    s2p[:, 1, 0] = traces_data[SParam.S21]
    s2p[:, 1, 1] = traces_data[SParam.S22]
    return rf.Network(f=freq_data/1E9, s=s2p, f_unit="GHz")
def convert_from_NR1(val: str) -> int:
    return int(val)
def convert_from_NR3(val: str) -> float:
    return float(val)
def convert_from_trace_data(val: str, format: str) -> List[str]:
    if len(val) < 2:
         return None
    len_dig_count = int(val[1])+2
    if len(val) <= len_dig_count:
         return None
    if format == DataFormat.ASCII:
        splited = val[len_dig_count:].split(",")
        if len(splited[-1]) == 0:
            return splited[:-1]
        else:
            return splited
    elif format == DataFormat.REAL32 or format == DataFormat.REAL64:
        num_size = 4
        if format == DataFormat.REAL64:
            num_size = 8
        data = []
        for i in range(len_dig_count, len(val), num_size):
            tmp = val[i:num_size]
    else:
        raise NotImplementedError(f"Converting from {format} format is not implemented!")
def convert_data_to_complex(data: List):
    real = np.asarray(data, dtype=float)
    if len(real) < 1:
        return np.ndarray(shape=(0))
    elif len(real)%2 == 1:
        real = np.append(real, 0)
    real = real.reshape((len(real)//2, 2))
    complex = real[:, 0] + real[:, 1]*1j
    return complex
def convert_header_to_dict(data: List[str]) -> Dict[str, str]:
    header = {}
    for record in data:
        splited = record.split("=")
        if len(splited) >= 2:
            header[splited[0]] = splited[1]
        elif len(splited) == 1 and len(splited[0]):
            header[splited[0]] = None
    return header

class VNA: 
    data_format = DataFormat.REAL32
    def __init__(self, resource_manager: pyvisa.ResourceManager, instrument_id: str):
        self.inst = resource_manager.open_resource(instrument_id)
    
    def __del___(self):
        if self.inst is not None:
            self.inst.close()
    
    def get_identification(self) -> str:
        return self.inst.query("*IDN?")

    def get_traces_data_as_s2p(self, check_traces_freq = False) -> rf.Network:
        data = {}
        freq = None
        default_timeout = self.inst.timeout
        self.inst.timeout = 10000
        for trace, sparam in TRACES_MAPPING.items():
            data[sparam] = self.get_trace_data(trace)
            if freq is None or check_traces_freq:
                trace_freq = self.get_trace_freq_data(trace)
                if freq is not None and (trace_freq != freq).any():
                    raise IOError(EXCEPTION_PREFIX + "Unable to readout traces data, frequency data differs between traces.")
                freq = trace_freq
        self.inst.timeout = default_timeout
        return convert_traces_data_to_s2p(data, freq)

    def set_traces_as_s2p(self) -> None:
        self.set_data_format(self.data_format)
        for trace, sparam in TRACES_MAPPING.items():
            #self.set_trace_domain(trace, Domain.FREQ)
            self.set_trace_spar(trace, sparam)
    def get_traces_count(self) -> int:
        return int(self.inst.query(":TRACE:TOT?"))
    def set_traces_count(self, traces_count: int) -> None:
        self.inst.write(f":TRACE:TOT {traces_count:d}")
    def get_data_format(self) -> str:
        return self.inst.query(":FORM:READ:DATA?")
    def set_data_format(self, data_format: str) -> None:
        self.inst.write(f":FORM:READ:DATA {data_format}")
    def get_trace_spar(self, trace_num: int) -> str:
        return self.inst.query(f":TRAC{trace_num}:SPAR?").lower()
    def set_trace_spar(self, trace_num: int, sparam: str) -> None:
        self.inst.write(f":TRAC{trace_num:d}:SPAR {sparam}")
    def get_trace_domain(self, trace_num: int) -> str:
        return self.inst.query(f":TRAC{trace_num:d}:DOM?")
    def set_trace_domain(self, trace_num: int, domain: str) -> None:
        self.inst.write(f":TRAC{trace_num:d}:DOM {domain}")
    def get_trace_data(self, trace_num: int) -> np.ndarray:
        datatype = None
        if self.data_format == DataFormat.REAL64:
            datatype = "d"
        elif self.data_format == DataFormat.REAL32:
            datatype = "f"
        resp = self.inst.query_binary_values(f":TRAC:DATA? {trace_num:d}", datatype=datatype)
        return convert_data_to_complex(resp)
    def get_trace_freq_data(self, trace_num: int) -> np.ndarray:
        if self.data_format == DataFormat.REAL64:
            datatype = "d"
        elif self.data_format == DataFormat.REAL32:
            datatype = "f"
        resp = self.inst.query_binary_values(f":SENS{trace_num:d}:FREQ:DATA?", datatype=datatype)
        return np.asarray(resp, dtype=float)
    def get_trace_header(self, trace_num: int) -> Dict[str, str]:
        resp = convert_from_trace_data(self.inst.query(f":TRAC:PRE? {trace_num:d}"), DataFormat.ASCII)
        return convert_header_to_dict(resp)

    def get_freq_settings(self) -> FrequencySettings:
        f_start = convert_from_NR3(self.inst.query(":FREQ:STAR?"))
        f_stop = convert_from_NR3(self.inst.query(":FREQ:STOP?"))
        points_num = convert_from_NR1(self.inst.query(":SENS:SWE:POIN?"))
        return FrequencySettings(f_start, f_stop, points_num)
    def set_freq_settings(self, f_start: float, f_stop: float, points_num: int) -> None:
        self.inst.write(f":FREQ:STAR {round(f_start):d}")
        self.inst.write(f":FREQ:STOP {round(f_stop):d}")
        self.inst.write(f":SENS:SWE:POIN {points_num:d}")

    def get_sweep_time(self) -> float:
        # TODO: Get sweep time based on IFBW and SWEEP NUMBER
        return 20
    def get_is_sweep_completed(self) -> bool:
        resp = self.inst.query(":STATus:OPERation?")
        return convert_from_NR1(resp) & 0b1<<8 > 0
    def get_is_sweep_continuous(self) -> bool:
        """Return True when VNA continuously sweeping or False when sweeping is hold"""
        resp = self.inst.query(":INIT:CONT?")
        return convert_from_NR1(resp) == 1
    def set_is_sweep_continuous(self, is_continuous: bool) -> None:
        self.inst.write(f":INIT:CONT {int(is_continuous)}")
    def start_sweep(self) -> None:
        self.inst.write(":INIT:IMM")
    def start_single_sweep_await(self) -> None:
        wait_time = 0.5
        self.start_sweep()
        time.sleep(wait_time)
        for i in range(0,100):
            if self.get_is_sweep_completed():
                return
            time.sleep(wait_time)
        if not self.get_is_sweep_completed():
            raise IOError(EXCEPTION_PREFIX + "Sweep isn't complete in expected amount of time.")

