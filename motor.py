"""A small class for one motor connected to a TB6612FNG driver."""

from gpiozero import OutputDevice, PWMOutputDevice


class TB6612Motor:
    def __init__(self, pwm_pin, in1_pin, in2_pin, reversed=False, trim=1.0, pin_factory=None):
        self.pwm = PWMOutputDevice(
            pwm_pin,
            frequency=1000,
            initial_value=0,
            pin_factory=pin_factory,
        )
        self.in1 = OutputDevice(
            in1_pin,
            initial_value=False,
            pin_factory=pin_factory,
        )
        self.in2 = OutputDevice(
            in2_pin,
            initial_value=False,
            pin_factory=pin_factory,
        )
        self.reversed = reversed
        self.trim = trim

    def set_speed(self, speed):
        speed = max(-1.0, min(1.0, float(speed)))

        if self.reversed:
            speed = -speed

        speed = max(-1.0, min(1.0, speed * self.trim))

        if speed > 0:
            self.in1.on()
            self.in2.off()
            self.pwm.value = speed
        elif speed < 0:
            self.in1.off()
            self.in2.on()
            self.pwm.value = abs(speed)
        else:
            self.stop()

    def stop(self):
        self.pwm.value = 0
        self.in1.off()
        self.in2.off()

    def close(self):
        self.stop()
        self.pwm.close()
        self.in1.close()
        self.in2.close()
