import pyvisa
import time
from vna_anritsu_MS20xxC_api import vna_api
from rotary_table_api import rotary_table_api as rt_api
from rotary_table_api import rotary_table_messages as rt_msg
 
# Initialize rotary table's and VNA APIs
rt = rt_api.RotaryTable(port_name="COM3", rs_converter=True)
visa_rm = pyvisa.ResourceManager()
vna = vna_api.VNA(visa_rm, instrument_id="USB0::0x0B5B::0xFFF9::1937045_1736_30::INSTR")

# Config variables
rt_id = 0
speed = 5
s2p_dir = "../tmp"
s2p_filename = "test"

# Halt RT in current position and set that position as 0deg
rt.send_request(rt_msg.RequestHalt(rt_id))
time.sleep(0.1)
rt.send_request(rt_msg.RequestSetHome(rt_id))

# Prepare VNA for reading measurements
vna.set_traces_as_s2p()
vna.set_is_sweep_continuous(False)

# Loop over angles
angle_step = 5
angle_points = range(0, 360, 5)
for angle in angle_points:
    print(f"angle={angle}deg")
    # Request rotate to position and wait until RT stopped
    rt.send_request(rt_msg.RequestRotate(rt_id, angle, speed))
    while(rt.send_request(rt_msg.RequestGetStatus(rt_id)).is_rotating):
        time.sleep(0.2)
    time.sleep(0.5)

    # Make single measurement, read it out and save in file
    vna.start_single_sweep_await()
    s2p = vna.get_traces_data_as_s2p() # get_traces_data_as_s2p() returns skrf.Network object that may be easily ploted 
    s2p.comments = f"angle={angle:f}deg"
    s2p.write_touchstone(f"{s2p_filename}_{angle}deg", s2p_dir, skrf_comment=False)

# Return to home position after last measurement
rt.send_request(rt_msg.RequestRotate(rt_id, 0, speed))
while(rt.send_request(rt_msg.RequestGetStatus(rt_id)).is_rotating):
    time.sleep(0.2)
