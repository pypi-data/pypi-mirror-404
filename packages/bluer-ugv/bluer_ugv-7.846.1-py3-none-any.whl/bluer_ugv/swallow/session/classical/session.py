from RPi import GPIO  # type: ignore
from queue import Empty

from bluer_options import string
from bluer_options.env import abcli_hostname
from bluer_options.timing.classes import Timing
from bluer_objects.env import abcli_object_name
from bluer_objects.metadata import post_to_object
from bluer_sbc.env import BLUER_SBC_CAMERA_KIND, BLUER_SBC_SWALLOW_HAS_STEERING
from bluer_sbc.session.functions import reply_to_bash

from bluer_ugv.README.ugvs.location import get_location
from bluer_ugv.swallow.session.classical.ethernet.classes import ClassicalEthernet
from bluer_ugv.swallow.session.classical.camera import (
    ClassicalCamera,
    ClassicalNavigationCamera,
    ClassicalTrackingCamera,
    ClassicalVoidCamera,
    ClassicalYoloCamera,
)
from bluer_ugv.swallow.session.classical.push_button import ClassicalPushButton
from bluer_ugv.swallow.session.classical.keyboard.classes import ClassicalKeyboard
from bluer_ugv.swallow.session.classical.leds import ClassicalLeds
from bluer_ugv.swallow.session.classical.mousepad import ClassicalMousePad
from bluer_ugv.swallow.session.classical.motor import (
    ClassicalLeftMotor,
    ClassicalRightMotor,
    ClassicalRearMotors,
    ClassicalSteeringMotor,
    ClassicalVoidMotor,
)
from bluer_ugv.swallow.session.classical.setpoint.classes import ClassicalSetPoint
from bluer_ugv.swallow.session.classical.setpoint.ethernet import (
    ClassicalEthernetSetPoint,
)
from bluer_ugv.swallow.session.classical.position import ClassicalPosition
from bluer_ugv.swallow.session.classical.screen.classes import ClassicalScreen
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.classes import (
    ClassicalUltrasonicSensor,
)
from bluer_ugv.swallow.session.classical.audio.classes import ClassicalAudio
from bluer_ugv.env import BLUER_UGV_MOUSEPAD_ENABLED
from bluer_ugv.logger import logger


class ClassicalSession:
    def __init__(
        self,
        object_name: str,
    ):
        self.object_name = object_name

        _, self.location = get_location(abcli_hostname)

        GPIO.setmode(GPIO.BCM)

        self.ethernet = ClassicalEthernet()

        self.leds = ClassicalLeds()

        self.audio = ClassicalAudio(
            leds=self.leds,
        )

        self.setpoint = (
            ClassicalSetPoint if self.location == "front" else ClassicalEthernetSetPoint
        )(
            ethernet=self.ethernet,
            leds=self.leds,
        )

        if BLUER_UGV_MOUSEPAD_ENABLED:
            self.mousepad = ClassicalMousePad(
                leds=self.leds,
                setpoint=self.setpoint,
            )

        self.keyboard = ClassicalKeyboard(
            ethernet=self.ethernet,
            leds=self.leds,
            setpoint=self.setpoint,
        )

        self.ultrasonic_sensor = ClassicalUltrasonicSensor(
            setpoint=self.setpoint,
            keyboard=self.keyboard,
        )

        self.push_button = ClassicalPushButton(
            leds=self.leds,
        )

        self.has_steering = BLUER_SBC_SWALLOW_HAS_STEERING == 1
        logger.info("has_steering: {}".format(self.has_steering))

        self.motor1 = (
            ClassicalVoidMotor
            if self.location != "front"
            else ClassicalSteeringMotor if self.has_steering else ClassicalRightMotor
        )(
            setpoint=self.setpoint,
            leds=self.leds,
        )

        self.motor2 = (
            ClassicalVoidMotor
            if self.location != "front"
            else ClassicalRearMotors if self.has_steering else ClassicalLeftMotor
        )(
            setpoint=self.setpoint,
            leds=self.leds,
        )

        if self.location == "front":
            logger.info(
                "wheel arrangement: {} + {}".format(
                    self.motor1.role,
                    self.motor2.role,
                )
            )
        else:
            logger.info("no wheels.")

        self.position = ClassicalPosition(object_name)

        camera_class = (
            ClassicalVoidCamera
            if BLUER_SBC_CAMERA_KIND == "void"
            else (
                ClassicalYoloCamera
                if BLUER_SBC_CAMERA_KIND == "yolo"
                else (
                    ClassicalTrackingCamera
                    if BLUER_SBC_CAMERA_KIND == "tracking"
                    else (
                        ClassicalNavigationCamera
                        if BLUER_SBC_CAMERA_KIND == "navigation"
                        else ClassicalCamera
                    )
                )
            )
        )
        logger.info(
            "camera: {} [{}]".format(
                camera_class.__name__,
                BLUER_SBC_CAMERA_KIND,
            )
        )
        self.camera = camera_class(
            keyboard=self.keyboard,
            leds=self.leds,
            setpoint=self.setpoint,
            object_name=self.object_name,
        )

        self.screen = ClassicalScreen()

        logger.info(
            "{}: created for {}".format(
                self.__class__.__name__,
                self.object_name,
            )
        )

        self.timing = Timing()

    def cleanup(self):
        self.audio.stop()
        self.ethernet.stop()
        self.ultrasonic_sensor.stop()
        self.camera.stop()

        self.motor1.cleanup()
        self.motor2.cleanup()

        self.camera.cleanup()

        GPIO.cleanup()

        self.timing.calculate()
        loop_frequency = round(
            1 / self.timing.stats["session.update"].get("average", -1),
            2,
        )
        self.timing.log()
        post_to_object(
            abcli_object_name,
            "timing",
            self.timing.as_dict,
        )
        logger.info(
            "loop frequency: {}".format(string.pretty_frequency(loop_frequency))
        )
        post_to_object(
            abcli_object_name,
            "loop_frequency",
            loop_frequency,
        )

        self.screen.cleanup()

        logger.info(f"{self.__class__.__name__}.cleanup")

    def initialize(self) -> bool:
        return all(
            thing.initialize()
            for thing in [
                self.screen,
                self.push_button,
                self.leds,
                self.motor1,
                self.motor2,
                self.camera,
                self.position,
            ]
        )

    def process_ethernet_messages(self) -> bool:
        while True:
            try:
                # pylint: disable=protected-access
                command = self.ethernet.client._receive_queue.get_nowait()
            except Empty:
                break

            if command.action == "keyboard":
                reply_to_bash(command.data.get("event", "unknown"))
                logger.info("stop received.")
                return False

            if command.action == "setpoint.put":
                self.setpoint.put(
                    value=command.data.get("value", 0),
                    what=command.data.get("what", "void"),
                    log=True,
                    steering_expires_in=command.data.get("steering_expires_in", 0),
                )
            else:
                logger.warning(f"unknown command: {command.as_str()}")

        return True

    def update(self) -> bool:
        self.timing.start("session.update")

        for thing in [
            self.keyboard,
            self.push_button,
            self.camera,
            self.position,
            self.setpoint,
            self.motor1,
            self.motor2,
            self.leds,
            self.screen,
        ]:
            self.timing.start(thing.__class__.__name__)

            if not thing.update():
                return False

            self.timing.stop(thing.__class__.__name__)

        self.timing.stop("session.update")

        return self.process_ethernet_messages()
