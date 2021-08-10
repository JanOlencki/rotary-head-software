from collections import namedtuple
from typing import Final

FrequencySettings = namedtuple("FrequencySettings", ("start", "stop", "points_num"))  

class SParam:
    S11: Final = "s11"
    S12: Final = "s12"
    S21: Final = "s21"
    S22: Final = "s22"

class Domain:
    FREQ: Final = "FREQ"
    TIME: Final = "TIME"
    DISTANCE: Final = "DIST"
    FREQ_GATE: Final = "FGT"

class DataFormat:
    ASCII: Final = "ASC"
    INT: Final = "INT,32"
    REAL32: Final = "REAL,32"
    REAL64: Final = "REAL,64"

