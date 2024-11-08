from limonata.actuators.base import Actuator
import serial


class ControlValve(Actuator):
    def __init__(self, sp: serial.Serial | None = None, debug: bool = False) -> None:
        super().__init__(sp, debug)

    def __enter__(self) -> "ControlValve":
        return self
    