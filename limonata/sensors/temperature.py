from limonata.actuators.base import Actuator
import serial


class Thermocouple(Actuator):
    def __init__(self, sp: serial.Serial, debug: bool = False, type: str = "K") -> None:
        super().__init__(sp, debug)
        self.type = type
        # self.link = "https://a.co/d/asBIGne"
        # self.voltage_rating = 12 # V
        # self.power_rating = 100 # W
        # self.current_rating = self.power_rating/self.voltage_rating # A

    def __enter__(self) -> "Thermocouple":
        return self
    
    @property
    def T(self) -> float:
        """Return a float denoting the temperature of the thermocouple."""
        return self.send_and_receive(msg="T", convert=float)
    