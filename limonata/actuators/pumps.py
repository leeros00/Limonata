from limonata.actuators.base import Actuator
import serial


class Pump(Actuator):
    def __init__(self, sp: serial.Serial, debug: bool = False) -> None:
        super().__init__(sp, debug)

    def __enter__(self) -> "Pump":
        return self
    

class BrushlessPump(Pump):
    def __init__(self, sp: serial.Serial, debug = False):
        super().__init__(sp, debug)

    def __enter__(self) -> "BrushlessPump":
        return self