# Pi Rover V1

Pi Rover V1 is a Raspberry Pi-based mobile robot controlled through a web
browser. It provides a live camera stream, optional YOLO object detection,
keyboard and touchscreen driving controls, a movable pan-and-tilt camera, and
a servo-operated trapdoor.

The project uses Flask for the web interface and control API, Picamera2 for
reliable Raspberry Pi camera capture, OpenCV for video processing, gpiozero for
hardware control, and Ultralytics YOLO for object detection. Safety features
include an automatic command watchdog that stops movement if communication
with the browser is interrupted.

## File map

- `app.py` is the starting point. It creates the web API, starts the camera and
  watchdog threads, and performs safe shutdown.
- `config.py` contains every pin number and tuning value.
- `calibrate_trapdoor.py` is the interactive trapdoor calibration utility.
- `calibration.py` loads and saves the calibrated trapdoor positions.
- `motor.py` knows how to control one TB6612FNG motor channel.
- `hardware.py` combines the two motors and three servos into simple actions
  such as `drive()`, `move_camera()`, and `set_trapdoor()`.
- `state.py` stores values shared by background threads and web requests. Its
  lock prevents two threads from changing a shared value at the same time.
- `detection.py` loads YOLO and converts its result into ordinary dictionaries.
- `camera.py` captures frames with Picamera2, asks YOLO to inspect selected
  frames, uses OpenCV to draw boxes, and creates the MJPEG video stream.
- `templates/index.html` is the page structure.
- `static/style.css` controls its appearance.
- `static/controls.js` handles keyboard/touch controls and sends API requests.

## How the program works

1. `main()` creates the GPIO hardware and optional YOLO detector.
2. It starts two daemon threads. The camera thread continuously captures
   frames. The watchdog thread continuously checks the last command time.
3. Flask serves the page and receives commands such as `POST /api/drive`.
4. The browser repeats movement commands every 120 ms while a key/button is
   held. If those commands disappear for more than 0.7 seconds, the watchdog
   stops the rover. This is an important safety feature.
5. The camera thread stores its newest annotated frame in shared state.
   `/video` repeatedly JPEG-encodes that frame and sends it as an MJPEG stream.
6. `/api/status` returns camera, YOLO, trapdoor, and detection information for
   the text above the video.

## Install and run

On Raspberry Pi OS:

```bash
sudo apt update
sudo apt install python3-opencv python3-gpiozero python3-picamera2
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install Flask ultralytics
python app.py
```

Then open `http://PI_ADDRESS:5000` on a device on the same network.

Using `--system-site-packages` lets the virtual environment see the Picamera2,
OpenCV, and GPIO packages installed by Raspberry Pi OS. This is normally more
reliable than trying to install Picamera2 entirely through pip.

## Raspberry Pi camera

The program requests a 640 × 480 `RGB888` stream from Picamera2. Picamera2
provides that buffer in the BGR byte order expected by OpenCV, so it can be
passed to OpenCV and YOLO without an extra color conversion.

Before starting the rover, test the camera using the Raspberry Pi camera tool:

```bash
rpicam-hello
```

On older Raspberry Pi OS releases the equivalent test command may be
`libcamera-hello`.

## Explanation of important code details

### Continuous and positional servos

Pan and tilt are continuous-rotation servos, so their values mean direction
and speed. `None` stops sending pulses. The trapdoor is positional, so it is
given a real angle. Tune pulse widths and angles carefully for your servos.

### Lock

Flask requests, camera capture, and the watchdog run at the same time. The
shared `state.lock` makes a small protected section where only one thread may
read/change related values.

### YOLO frame skipping

Detection is expensive. It runs every third frame, while the most recent boxes
are drawn on the frames between detections. Increase
`RUN_YOLO_EVERY_N_FRAMES` if the Pi becomes slow or hot.

### API validation

The drive and camera routes catch non-numeric input and return HTTP 400 rather
than allowing malformed browser input to crash a request handler.

## Calibrating the trapdoor

The included utility lets you command the servo to the required positions and
then remember them:

1. Stop `app.py` so that two programs do not try to use GPIO 19.
2. Run `python3 calibrate_trapdoor.py`.
3. Enter `+` or `-` to move in five-degree steps. You can also enter an exact
   angle such as `72`.
4. At the desired closed position, enter `c`.
5. At the desired open position, enter `o`.
6. Enter `s` to save, then `q` to quit.

The utility creates `trapdoor_calibration.json` in the project folder. The main
rover automatically loads this file at startup. If the file is missing or
invalid, it safely falls back to the angles in `config.py`.
