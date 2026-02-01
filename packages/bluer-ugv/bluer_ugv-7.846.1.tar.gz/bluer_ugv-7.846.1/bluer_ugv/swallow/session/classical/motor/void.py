from bluer_ugv.swallow.session.classical.leds import ClassicalLeds
from bluer_ugv.swallow.session.classical.setpoint.classes import ClassicalSetPoint


class ClassicalVoidMotor:
    def __init__(
        self,
        setpoint: ClassicalSetPoint,
        leds: ClassicalLeds,
    ):
        pass

    def cleanup(self):
        pass

    def initialize(self) -> bool:
        return True

    def update(self) -> bool:
        return True
