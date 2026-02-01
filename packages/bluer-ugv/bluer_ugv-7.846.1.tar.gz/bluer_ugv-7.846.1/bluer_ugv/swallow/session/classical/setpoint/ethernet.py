from typing import Union, Dict

from bluer_ugv.swallow.session.classical.ethernet.command import EthernetCommand
from bluer_ugv.swallow.session.classical.setpoint.classes import ClassicalSetPoint


class ClassicalEthernetSetPoint(ClassicalSetPoint):
    def put(
        self,
        value: Union[int, bool, Dict[str, Union[int, bool]]],
        what: str = "all",
        log: bool = True,
        steering_expires_in: float = 0,
    ):
        super().put(
            value=value,
            what=what,
            log=log,
            steering_expires_in=steering_expires_in,
        )

        self.ethernet.client.send(
            EthernetCommand(
                action="setpoint.put",
                data={
                    "value": value,
                    "what": what,
                    "steering_expires_in": steering_expires_in,
                },
            )
        )
