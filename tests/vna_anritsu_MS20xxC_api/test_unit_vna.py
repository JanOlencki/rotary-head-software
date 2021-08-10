from vna_anritsu_MS20xxC_api import vna_api
from vna_anritsu_MS20xxC_api.vna_types import DataFormat

def test_checking_device_indentification():
    assert vna_api.is_instrument_supported("\"Anritsu,MS2028C/10/2,62011032,1.23\"") == True
    assert vna_api.is_instrument_supported("\"Anritsu,MS102333C/10/2,62011032,1.23\"") == False
    assert vna_api.is_instrument_supported("\"Anritsu,te\"") == False
    assert vna_api.is_instrument_supported("\"Anritsu\"") == False
    assert vna_api.is_instrument_supported("ee") == False
    assert vna_api.is_instrument_supported("") == False

def test_converting_trace_data():
    assert vna_api.convert_from_trace_data("#", DataFormat.ASCII) == None
    assert vna_api.convert_from_trace_data("#0", DataFormat.ASCII) == None
    assert vna_api.convert_from_trace_data("#1", DataFormat.ASCII) == None
    assert vna_api.convert_from_trace_data("#12", DataFormat.ASCII) == None
    assert vna_api.convert_from_trace_data("#12test", DataFormat.ASCII) == ["test"]
    assert vna_api.convert_from_trace_data("#242test", DataFormat.ASCII) == ["test"]
    assert vna_api.convert_from_trace_data("#242test,", DataFormat.ASCII) == ["test"]
    assert vna_api.convert_from_trace_data("#242test,test", DataFormat.ASCII) == ["test","test"]

    assert (vna_api.convert_data_to_complex([]) == []).all()
    assert (vna_api.convert_data_to_complex([1]) == [1+0j]).all()
    assert (vna_api.convert_data_to_complex([1,1]) == [1+1j]).all()
    assert (vna_api.convert_data_to_complex([1,1,2,3]) == [1+1j, 2+3j]).all()

    assert vna_api.convert_header_to_dict([""]) == {}
    assert vna_api.convert_header_to_dict(["test"]) == {"test": None}
    assert vna_api.convert_header_to_dict(["test=321"]) == {"test": "321"}
    assert vna_api.convert_header_to_dict(["test=321","test2=2"]) == {"test": "321", "test2": "2"}
