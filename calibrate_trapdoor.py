#Interactive trapdoor calibration tool.

from time import sleep
from gpiozero import AngularServo
from gpiozero.pins.lgpio import LGPIOFactory
import config
from calibration import CALIBRATION_FILE, load_trapdoor_angles, save_trapdoor_angles


MIN_SAFE_ANGLE = 0
MAX_SAFE_ANGLE = 180
STARTING_STEP = 5

def limit_angle(angle):
    return max(MIN_SAFE_ANGLE, min(MAX_SAFE_ANGLE, angle))


def print_help():
    print("\nCommands:")
    print("  + or r   move 5 degrees higher")
    print("  - or l   move 5 degrees lower")
    print("  number   move to that angle, for example: 75")
    print("  o        remember current angle as OPEN")
    print("  c        remember current angle as CLOSED")
    print("  s        save OPEN and CLOSED angles")
    print("  q        quit")
    print("  h        show this help\n")


def main():
    saved = load_trapdoor_angles()
    closed_angle = saved["closed_angle"]
    open_angle = saved["open_angle"]
    current_angle = closed_angle
    step = STARTING_STEP

    pin_factory = LGPIOFactory()
    servo = AngularServo(
        config.TRAPDOOR_SERVO_PIN,
        min_angle=MIN_SAFE_ANGLE,
        max_angle=MAX_SAFE_ANGLE,
        min_pulse_width=0.0005,
        max_pulse_width=0.0025,
        initial_angle=current_angle,
        pin_factory=pin_factory,
    )

    print("Trapdoor calibration")
    print("Keep fingers and loose objects away from the mechanism.")
    print("Stop immediately if the servo buzzes or pushes against a hard stop.")
    print_help()

    try:
        while True:
            print(
                f"Current: {current_angle:.1f}° | "
                f"CLOSED: {closed_angle:.1f}° | OPEN: {open_angle:.1f}°"
            )
            command = input("calibration> ").strip().lower()

            if command in ("+", "r"):
                current_angle = limit_angle(current_angle + step)
            elif command in ("-", "l"):
                current_angle = limit_angle(current_angle - step)
            elif command == "o":
                open_angle = current_angle
                print("Current angle remembered as OPEN")
                continue
            elif command == "c":
                closed_angle = current_angle
                print("Current angle remembered as CLOSED")
                continue
            elif command == "s":
                save_trapdoor_angles(closed_angle, open_angle)
                print("Saved calibration to:", CALIBRATION_FILE)
                continue
            elif command == "h":
                print_help()
                continue
            elif command == "q":
                break
            else:
                try:
                    requested_angle = float(command)
                    if not MIN_SAFE_ANGLE <= requested_angle <= MAX_SAFE_ANGLE:
                        print("Enter an angle from 0 to 180")
                        continue
                    current_angle = requested_angle
                except ValueError:
                    print("Unknown command. Enter h for help.")
                    continue

            servo.angle = current_angle
            sleep(0.3)
    finally:
        # None stops control pulses. The trapdoor mechanism must be able to
        # hold safely when servo power/control is released.
        servo.angle = None
        servo.close()
        pin_factory.close()
        print("Servo released. Calibration program stopped.")
if __name__ == "__main__":
    main()
