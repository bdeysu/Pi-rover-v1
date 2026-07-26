"""GPIO hardware setup."""

from time import time

from gpiozero import AngularServo, OutputDevice, Servo

import config
from calibration import load_trapdoor_angles
from motor import TB6612Motor
from state import state


class RoverHardware:
    def __init__(self):
        self.trapdoor_angles = load_trapdoor_angles()
        self.standby = OutputDevice(config.STBY_PIN, initial_value=True)

        self.left_motor = TB6612Motor(
            config.LEFT_PWM_PIN,
            config.LEFT_IN1_PIN,
            config.LEFT_IN2_PIN,
            reversed=config.LEFT_MOTOR_REVERSED,
            trim=config.LEFT_TRIM,
        )
        self.right_motor = TB6612Motor(
            config.RIGHT_PWM_PIN,
            config.RIGHT_IN1_PIN,
            config.RIGHT_IN2_PIN,
            reversed=config.RIGHT_MOTOR_REVERSED,
            trim=config.RIGHT_TRIM,
        )

        # These are continuous-rotation servos. Their value controls speed,
        # not angle. None stops the control pulses and normally stops movement.
        self.pan_servo = Servo(
            config.PAN_SERVO_PIN,
            min_pulse_width=0.0005,
            max_pulse_width=0.0025,
            initial_value=None,
        )
        self.tilt_servo = Servo(
            config.TILT_SERVO_PIN,
            min_pulse_width=0.0005,
            max_pulse_width=0.0025,
            initial_value=None,
        )
        self.trapdoor_servo = AngularServo(
            config.TRAPDOOR_SERVO_PIN,
            min_angle=0,
            max_angle=180,
            min_pulse_width=0.0005,
            max_pulse_width=0.0025,
            initial_angle=self.trapdoor_angles["closed_angle"],
        )

    def drive(self, left_speed, right_speed):
        left_speed = max(-1.0, min(1.0, float(left_speed)))
        right_speed = max(-1.0, min(1.0, float(right_speed)))

        with state.lock:
            state.last_drive_command_time = time()
            self.standby.on()
            self.left_motor.set_speed(left_speed)
            self.right_motor.set_speed(right_speed)

    def move_camera(self, pan, tilt):
        pan = max(-1.0, min(1.0, float(pan)))
        tilt = max(-1.0, min(1.0, float(tilt)))

        if config.PAN_REVERSED:
            pan = -pan
        if config.TILT_REVERSED:
            tilt = -tilt

        with state.lock:
            state.last_camera_command_time = time()
            self.pan_servo.value = None if pan == 0 else pan * config.CAMERA_SERVO_SPEED
            self.tilt_servo.value = None if tilt == 0 else tilt * config.CAMERA_SERVO_SPEED

    def stop_motors(self):
        self.left_motor.stop()
        self.right_motor.stop()

    def stop_camera(self):
        self.pan_servo.value = None
        self.tilt_servo.value = None

    def stop_all(self):
        self.stop_motors()
        self.stop_camera()

    def set_trapdoor(self, should_open):
        angle = (
            self.trapdoor_angles["open_angle"]
            if should_open
            else self.trapdoor_angles["closed_angle"]
        )
        with state.lock:
            self.trapdoor_servo.angle = angle
            state.trapdoor_open = should_open

    def toggle_trapdoor(self):
        with state.lock:
            should_open = not state.trapdoor_open
        self.set_trapdoor(should_open)

    def close(self):
        self.stop_all()
        self.set_trapdoor(False)
        self.standby.off()
        self.left_motor.close()
        self.right_motor.close()
        self.pan_servo.close()
        self.tilt_servo.close()
        self.trapdoor_servo.close()
        self.standby.close()
