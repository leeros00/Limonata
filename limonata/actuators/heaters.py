from limonata.actuators.base import Actuator
import serial


class Heater(Actuator):
    def __init__(self, sp: serial.Serial, debug: bool = False) -> None:
        super().__init__(sp, debug)
        self.link = "https://a.co/d/asBIGne"
        self.voltage_rating = 12 # V
        self.power_rating = 100 # W
        self.current_rating = self.power_rating/self.voltage_rating # A

    def __enter__(self) -> "Heater":
        return self