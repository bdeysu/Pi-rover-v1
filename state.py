"""Thread-safe values shared by the camera, watchdog, and Flask routes."""

from threading import Lock


class RoverState:
    def __init__(self):
        self.lock = Lock()
        self.running = True
        self.latest_frame = None
        self.latest_detections = []
        self.camera_ok = False
        self.trapdoor_open = False
        self.last_drive_command_time = 0.0
        self.last_camera_command_time = 0.0


state = RoverState()
