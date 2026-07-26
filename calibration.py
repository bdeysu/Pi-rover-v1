"""Load and save user-calibrated trapdoor angles."""

import json
from pathlib import Path

import config


CALIBRATION_FILE = Path(__file__).with_name("trapdoor_calibration.json")


def default_angles():
    return {
        "closed_angle": config.TRAPDOOR_CLOSED_ANGLE,
        "open_angle": config.TRAPDOOR_OPEN_ANGLE,
    }


def load_trapdoor_angles():
    """Return saved angles, or config.py defaults if no valid file exists."""
    angles = default_angles()

    try:
        saved = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
        closed_angle = float(saved["closed_angle"])
        open_angle = float(saved["open_angle"])

        if not 0 <= closed_angle <= 180 or not 0 <= open_angle <= 180:
            raise ValueError("angles must be between 0 and 180")

        angles["closed_angle"] = closed_angle
        angles["open_angle"] = open_angle
    except FileNotFoundError:
        print("No trapdoor calibration file found; using config.py angles")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print("Invalid trapdoor calibration file; using config.py angles:", error)

    return angles


def save_trapdoor_angles(closed_angle, open_angle):
    data = {
        "closed_angle": float(closed_angle),
        "open_angle": float(open_angle),
    }
    CALIBRATION_FILE.write_text(
        json.dumps(data, indent=4) + "\n",
        encoding="utf-8",
    )

