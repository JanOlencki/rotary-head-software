import pytest
from rotary_table_api import rotary_table_messages as rt_msg

def test_simple_messages():
    msg = rt_msg.RequestGetStatus(0x2)
    assert msg.to_bytes() == b"\x5D\x20\0\0\0\xC0"

    msg = rt_msg.RequestSetHome(0x3)
    assert msg.to_bytes() == b"\x5D\x31\0\0\0\xB1"
    
    msg = rt_msg.RequestHalt(0x5)
    assert msg.to_bytes() == b"\x5D\x52\0\0\0\xDE"

    msg = rt_msg.RequestDisable(0x7)
    assert msg.to_bytes() == b"\x5D\x73\0\0\0\x06"

def set_rt_msg_constants():
    rt_msg.RPM_PRECISION = 0.5
    rt_msg.SPEED_MAX = 2**7
    rt_msg.RPM_MAX = rt_msg.SPEED_MAX/rt_msg.RPM_PRECISION
    rt_msg.ANGLE_FRACTION_LENGTH = 7
    rt_msg.ANGLE_PRECISION = 2**-3

def test_rotate_message():
    set_rt_msg_constants()
    msg = rt_msg.RequestRotate(0x2, 0, 16)
    assert msg.to_bytes() == b"\x5D\x24\x00\x00\x20\x78"
    msg = rt_msg.RequestRotate(0x3, 0.375, -16)
    assert msg.to_bytes() == b"\x5D\x34\x00\x30\xE0\xA8"
    msg = rt_msg.RequestRotate(0x3, -89.378, -16.2)
    assert msg.to_bytes() == b"\x5D\x34\x87\x50\xE0\x40"

def test_messages_fields():
    set_rt_msg_constants()
    msg = rt_msg.RequestGetStatus(0x2)
    assert msg.address == 2
    with pytest.raises(ValueError):
        msg.address = 16

    msg = rt_msg.RequestRotate(0x2, 0, 10)
    assert msg.angle == 0
    msg.angle = 361
    assert msg.angle == 1
    msg.angle = -270
    assert msg.angle == 90
    
    msg.angle = 90.125
    assert msg.angle == 90.125
    msg.angle = 90.123
    assert msg.angle == 90.125
    msg.angle = 90.21
    assert msg.angle == 90.25

    with pytest.raises(ValueError):
        msg.rpm = 1000
    msg.rpm = 10
    assert msg.rpm == 10
    msg.rpm = -1.5
    assert msg.rpm == -1.5
    msg.rpm = -1.76
    assert msg.rpm == -2

def test_reponses():
    with pytest.raises(ValueError):
        rt_msg.parse_response(b"\x53\x70\x00\x00\x37")
    resp = rt_msg.parse_response(b"\x5D\x00\x00\x00\x00\x00\x00\x00\x00")
    assert isinstance(resp, rt_msg.Response)
    assert not resp.is_valid
    resp = rt_msg.parse_response(b"\x5D\x0E\x00\x00\x00\x00\x00\x00\x00")
    assert isinstance(resp, rt_msg.ResponseConverterStatus)
    resp = rt_msg.parse_response(b"\x5D\x0F\x00\x00\x00\x00\x00\x00\x00")
    assert isinstance(resp, rt_msg.ResponseMotorStatus)

    resp = rt_msg.parse_response(b"\x5D\xD0\x00\x00\x00\x00\x00\x00\x2D")
    assert isinstance(resp, rt_msg.Response)
    assert resp.address == 0xD
    assert not resp.is_valid
    assert not rt_msg.parse_response(b"\x53\x70\x00\x00\x00\x00\x00\x00\x37").is_valid
    resp = rt_msg.parse_response(b"\x5D\x70\x00\x00\x00\x00\x00\x00\x1B")
    assert resp.address == 0x7
    assert resp.response_header == 0x0
    assert resp.is_valid

    resp = rt_msg.parse_response(b"\x5D\xCE\x01\x72\xDE\xAD\xBE\xEF\x7C")
    assert isinstance(resp, rt_msg.ResponseConverterStatus)
    assert resp.is_valid
    assert resp.status == 0x01
    assert resp.is_voltage_OK
    assert resp.voltage == 7.125
    assert resp.reserved_data == b"\xDE\xAD\xBE\xEF"
    
    resp = rt_msg.parse_response(b"\x5D\xAF\xF5\x91\xD0\x29\xA0\xD1\x1E")
    assert isinstance(resp, rt_msg.ResponseMotorStatus)
    assert resp.status == 0xF5
    assert resp.is_motor_OK
    assert not resp.is_rotating
    assert resp.is_enabled
    assert not resp.is_crc_valid
    assert resp.current_angle == 291.625
    assert resp.target_angle == 83.25
    assert resp.rpm == -23.5


