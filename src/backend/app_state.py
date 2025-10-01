from enum import Enum

class AppStates(Enum):
    WRITE_WAY = 0
    WAITING = 1

class GlobalState():
    _self = None
    _is_init = False
    
    def __new__(cls):
        if cls._self != None:
            cls._self = super().__new__(cls)
        return cls._self
    
    def __init__(self):
        if not self._is_init:
            self._cur_state = AppStates.WAITING
            
    def get_state(self) -> AppStates:
        return self._cur_state