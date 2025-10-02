from dataclasses import dataclass
import os

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
STATIONS_PATH = os.path.join(CUR_DIR, "data", "stations")

@dataclass
class Position():
    x: float
    y: float
    
@dataclass
class StationRssi():
    name: str
    rssi: int
    
def check_stations_path() -> bool:
    return os.path.exists(STATIONS_PATH)
    
def get_board_pos(data: list[StationRssi]) -> Position:
    pass

