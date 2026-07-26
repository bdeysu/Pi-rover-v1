"""Picamera2 capture, YOLO processing, and OpenCV MJPEG generation."""

from time import sleep

import cv2
import numpy as np
from picamera2 import Picamera2

import config
from state import state


class PiCamera:
    def __init__(self, detector):
        self.detector = detector
        self.camera = None

    def open(self):
        self.camera = Picamera2()
        camera_config = self.camera.create_video_configuration(
            main={
                "size": (config.CAMERA_WIDTH, config.CAMERA_HEIGHT),
                # Picamera2's RGB888 buffer is laid out as B, G, R bytes,
                # which is the channel order OpenCV expects.
                "format": "RGB888",
            },
            controls={"FrameRate": config.CAMERA_FPS},
        )
        self.camera.configure(camera_config)
        self.camera.start()
        sleep(1)

    def run(self):
        frame_number = 0
        previous_detections = []

        try:
            self.open()
            with state.lock:
                state.camera_ok = True
            print("Picamera2 camera started")

            while state.running:
                frame = self.camera.capture_array()

                frame_number += 1
                if frame_number % config.RUN_YOLO_EVERY_N_FRAMES == 0:
                    previous_detections = self.detector.detect(frame)

                self.draw_detections(frame, previous_detections)

                with state.lock:
                    state.latest_frame = frame.copy()
                    state.latest_detections = previous_detections.copy()
        except Exception as error:
            print("Camera stopped:", error)
        finally:
            with state.lock:
                state.camera_ok = False
            if self.camera is not None:
                try:
                    self.camera.stop()
                    self.camera.close()
                except Exception as error:
                    print("Camera cleanup warning:", error)

    @staticmethod
    def draw_detections(frame, detections):
        for item in detections:
            x1, y1, x2, y2 = item["box"]
            label = f'{item["name"]} {item["conf"]:.2f}'
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
            )


def generate_video_stream():
    while state.running:
        with state.lock:
            frame = None if state.latest_frame is None else state.latest_frame.copy()

        if frame is None:
            frame = np.zeros((config.CAMERA_HEIGHT, config.CAMERA_WIDTH, 3), dtype=np.uint8)
            cv2.putText(
                frame,
                "Camera not ready",
                (150, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )

        success, buffer = cv2.imencode(".jpg", frame)
        if success:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )
        sleep(0.03)
