"""Main program: builds the Flask API and starts background workers."""

import signal
from threading import Thread
from time import sleep, time

from flask import Flask, Response, jsonify, render_template, request

import config
from camera import PiCamera, generate_video_stream
from detection import ObjectDetector
from hardware import RoverHardware
from state import state

app = Flask(__name__)
hardware = None
detector = None


def json_body():
    return request.get_json(silent=True) or {}


@app.get("/")
def index():
    return render_template(
        "index.html",
        drive_speed=config.DRIVE_SPEED,
        turn_speed=config.TURN_SPEED,
    )


@app.get("/video")
def video():
    return Response(
        generate_video_stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/api/drive")
def api_drive():
    data = json_body()
    left = data.get("left", 0)
    right = data.get("right", 0)
    try:
        hardware.drive(left, right)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="left and right must be numbers"), 400
    return jsonify(ok=True, left=left, right=right)


@app.post("/api/camera")
def api_camera():
    data = json_body()
    pan = data.get("pan", 0)
    tilt = data.get("tilt", 0)
    try:
        hardware.move_camera(pan, tilt)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="pan and tilt must be numbers"), 400
    return jsonify(ok=True, pan=pan, tilt=tilt)


@app.post("/api/trapdoor/<action>")
def api_trapdoor(action):
    if action == "open":
        hardware.set_trapdoor(True)
    elif action == "close":
        hardware.set_trapdoor(False)
    elif action == "toggle":
        hardware.toggle_trapdoor()
    else:
        return jsonify(ok=False, error="unknown trapdoor action"), 404

    with state.lock:
        is_open = state.trapdoor_open
    return jsonify(ok=True, trapdoor_open=is_open)


@app.post("/api/stop")
def api_stop():
    with state.lock:
        hardware.stop_all()
    return jsonify(ok=True)


@app.get("/api/status")
def api_status():
    with state.lock:
        return jsonify(
            ok=True,
            camera_ok=state.camera_ok,
            yolo_enabled=detector.enabled,
            detections=state.latest_detections.copy(),
            trapdoor_open=state.trapdoor_open,
        )


def watchdog_loop():
    while state.running:
        now = time()
        with state.lock:
            if now - state.last_drive_command_time > config.COMMAND_TIMEOUT_SECONDS:
                hardware.stop_motors()
            if now - state.last_camera_command_time > config.COMMAND_TIMEOUT_SECONDS:
                hardware.stop_camera()
        sleep(0.05)


def shutdown(*_arguments):
    state.running = False
    if hardware is not None:
        hardware.close()


def main():
    global hardware, detector

    hardware = RoverHardware()
    detector = ObjectDetector()
    camera = PiCamera(detector)

    hardware.stop_all()
    hardware.set_trapdoor(False)

    Thread(target=watchdog_loop, daemon=True).start()
    Thread(target=camera.run, daemon=True).start()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"Pi Rover running at http://<raspberry-pi-ip>:{config.WEB_PORT}")
    try:
        app.run(
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            debug=False,
            threaded=True,
        )
    finally:
        shutdown()


if __name__ == "__main__":
    main()
