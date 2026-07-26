const pressedKeys = new Set();
const driveSpeed = Number(document.body.dataset.driveSpeed);
const turnSpeed = Number(document.body.dataset.turnSpeed);

let driveTimer = null;
let cameraTimer = null;

async function post(url, data = {}) {
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error("Request failed");
    } catch (error) {
        document.querySelector("#status").textContent = "Connection error";
    }
}

function repeatCommand(kind, values) {
    stopRepeating(kind);
    const url = kind === "drive" ? "/api/drive" : "/api/camera";
    post(url, values);
    const timer = setInterval(() => post(url, values), 120);
    if (kind === "drive") driveTimer = timer;
    else cameraTimer = timer;
}

function stopRepeating(kind) {
    if (kind === "drive") {
        clearInterval(driveTimer);
        driveTimer = null;
        post("/api/drive", {left: 0, right: 0});
    } else {
        clearInterval(cameraTimer);
        cameraTimer = null;
        post("/api/camera", {pan: 0, tilt: 0});
    }
}

function updateKeyboard() {
    let forward = 0;
    let turn = 0;
    if (pressedKeys.has("w")) forward += 1;
    if (pressedKeys.has("s")) forward -= 1;
    if (pressedKeys.has("a")) turn -= 1;
    if (pressedKeys.has("d")) turn += 1;

    if (forward || turn) {
        const left = Math.max(-1, Math.min(1, forward * driveSpeed + turn * turnSpeed));
        const right = Math.max(-1, Math.min(1, forward * driveSpeed - turn * turnSpeed));
        repeatCommand("drive", {left, right});
    } else {
        stopRepeating("drive");
    }

    let pan = 0;
    let tilt = 0;
    if (pressedKeys.has("ArrowLeft")) pan -= 1;
    if (pressedKeys.has("ArrowRight")) pan += 1;
    if (pressedKeys.has("ArrowUp")) tilt += 1;
    if (pressedKeys.has("ArrowDown")) tilt -= 1;

    if (pan || tilt) repeatCommand("camera", {pan, tilt});
    else stopRepeating("camera");
}

document.addEventListener("keydown", event => {
    if (event.repeat) return;
    const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
    const controlled = ["w", "a", "s", "d", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"];
    if (controlled.includes(key) || key === " ") event.preventDefault();

    if (key === " ") {
        pressedKeys.clear();
        stopRepeating("drive");
        stopRepeating("camera");
        post("/api/stop");
    } else if (["o", "c", "t"].includes(key)) {
        const action = {o: "open", c: "close", t: "toggle"}[key];
        post(`/api/trapdoor/${action}`);
    } else if (controlled.includes(key)) {
        pressedKeys.add(key);
        updateKeyboard();
    }
});

document.addEventListener("keyup", event => {
    const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
    pressedKeys.delete(key);
    updateKeyboard();
});

const driveValues = {
    forward: {left: driveSpeed, right: driveSpeed},
    backward: {left: -driveSpeed, right: -driveSpeed},
    left: {left: -turnSpeed, right: turnSpeed},
    right: {left: turnSpeed, right: -turnSpeed}
};
const cameraValues = {
    up: {pan: 0, tilt: 1}, down: {pan: 0, tilt: -1},
    left: {pan: -1, tilt: 0}, right: {pan: 1, tilt: 0}
};

function addHoldControls(selector, kind, values) {
    document.querySelectorAll(selector).forEach(button => {
        button.addEventListener("pointerdown", event => {
            event.preventDefault();
            repeatCommand(kind, values[button.dataset[kind]]);
        });
        ["pointerup", "pointerleave", "pointercancel"].forEach(name => {
            button.addEventListener(name, () => stopRepeating(kind));
        });
    });
}

addHoldControls("[data-drive]", "drive", driveValues);
addHoldControls("[data-camera]", "camera", cameraValues);
document.querySelector("#stop").addEventListener("click", () => post("/api/stop"));
document.querySelector("#camera-stop").addEventListener("click", () => stopRepeating("camera"));
document.querySelectorAll("[data-door]").forEach(button => {
    button.addEventListener("click", () => post(`/api/trapdoor/${button.dataset.door}`));
});

setInterval(async () => {
    try {
        const data = await (await fetch("/api/status")).json();
        const names = data.detections.map(item => item.name).join(", ");
        document.querySelector("#status").textContent =
            `Camera: ${data.camera_ok ? "ON" : "OFF"} | ` +
            `YOLO: ${data.yolo_enabled ? "ON" : "OFF"} | ` +
            `Trapdoor: ${data.trapdoor_open ? "OPEN" : "CLOSED"}` +
            (names ? ` | Detected: ${names}` : "");
    } catch (error) {
        document.querySelector("#status").textContent = "Connection error";
    }
}, 500);

window.addEventListener("beforeunload", () => navigator.sendBeacon("/api/stop"));
