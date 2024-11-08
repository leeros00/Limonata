from limonata.actuators.base import Actuator
import serial

class Agitator(Actuator):
    def __init__(self, sp: serial.Serial, debug: bool = False) -> None:
        super().__init__(sp, debug)

    def __enter__(self) -> "Agitator":
        return self