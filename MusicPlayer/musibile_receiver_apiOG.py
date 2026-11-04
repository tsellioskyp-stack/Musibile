import os
import threading
import sys
import vlc
from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
import time

current_file = None
LIBRARY_PATH = Path(sys.argv[2]).resolve()


def resolve_track_path(relative_path):
    if not relative_path:
        return None

    relative_path = relative_path.replace("\\", "/")

    # Remove the /songs/ URL prefix.
    if not relative_path.startswith("/songs/"):
        return None

    relative_path = relative_path[len("/songs/") :]

    track_path = Path(relative_path)

    if ".." in track_path.parts:
        return None

    full_path = (LIBRARY_PATH / track_path).resolve()

    try:
        full_path.relative_to(LIBRARY_PATH)
    except ValueError:
        return None

    return full_path if full_path.is_file() else None


app = Flask(__name__)
CORS(app)

# Initialize VLC
instance = vlc.Instance("--no-video")
player = instance.media_player_new()

# Protect playback operations from simultaneous requests
player_lock = threading.Lock()
# Shared playback session
session_lock = threading.Lock()

session = {
    "track": None,
    "output": "browser",  # "browser" or "laptop"
    "playing": False,
    "position": 0.0,  # seconds
    "duration": 0.0,  # seconds
    "volume": 1.0,  # 0.0 - 1.0
    "updated_at": time.time(),
    "command_id": 0,
    "command": None,
    "browser_id": None,
}

current_file = None


@app.route("/status", methods=["GET"])
def status():

    with player_lock:
        return jsonify(
            {
                "file": current_file,
                "state": str(player.get_state()),
                "playing": bool(player.is_playing()),
                "position_ms": player.get_time(),
                "duration_ms": player.get_length(),
                "volume": player.audio_get_volume(),
            }
        )


@app.route("/session/report", methods=["POST"])
def report_session():
    data = request.get_json(silent=True) or {}

    try:
        position = max(0.0, float(data.get("position", 0)))
        duration = max(0.0, float(data.get("duration", 0)))
        volume = max(0.0, min(1.0, float(data.get("volume", 1))))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid playback values"}), 400

    with session_lock:
        # Only the browser currently selected as output can report playback.
        if (
            session["output"] != "browser"
            or data.get("browser_id") != session["browser_id"]
        ):
            return jsonify({"ignored": True})

        session.update(
            {
                "track": data.get("track"),
                "playing": bool(data.get("playing", False)),
                "position": position,
                "duration": duration,
                "volume": volume,
                "updated_at": time.time(),
            }
        )

    return jsonify({"success": True})


@app.route("/session", methods=["GET"])
def get_session():
    with session_lock:
        state = session.copy()

    # Estimate the current position between browser updates.
    if state["playing"]:
        elapsed = time.time() - state["updated_at"]
        state["position"] += elapsed

    if state["duration"] > 0:
        state["position"] = min(state["position"], state["duration"])

    return jsonify(state)


@app.route("/session/command", methods=["POST"])
def session_command():
    data = request.get_json(silent=True) or {}

    command = data.get("command")
    allowed_commands = {"play", "pause", "resume", "seek", "volume", "stop"}

    if command not in allowed_commands:
        return jsonify({"error": "Invalid command"}), 400

    with session_lock:
        if session["output"] != "browser":
            return jsonify({"error": "Laptop output is not implemented yet"}), 409

        session["command_id"] += 1

        session["command"] = {
            "id": session["command_id"],
            "name": command,
            "data": data,
        }

    return jsonify({"success": True, "command_id": session["command_id"]})


@app.route("/session/ack", methods=["POST"])
def acknowledge_command():
    data = request.get_json(silent=True) or {}
    command_id = data.get("command_id")

    with session_lock:
        current_command = session["command"]

        if current_command and current_command["id"] == command_id:
            session["command"] = None

    return jsonify({"success": True})


@app.route("/session/claim", methods=["POST"])
def claim_browser():
    data = request.get_json(silent=True) or {}
    browser_id = data.get("browser_id")

    if not browser_id:
        return jsonify({"error": "Missing browser ID"}), 400

    with session_lock:
        session["browser_id"] = browser_id
        session["output"] = "browser"

    return jsonify({"success": True})


@app.route("/play", methods=["POST"])
def play():
    global current_file

    data = request.get_json(silent=True) or {}
    relative_path = data.get("path", "")

    resolved_path = resolve_track_path(relative_path)

    if resolved_path is None:
        return jsonify({"error": "Invalid path or file not found"}), 404

    with player_lock:
        if current_file == relative_path and player.get_state() == vlc.State.Paused:
            result = player.play()
        else:
            media = instance.media_new(str(resolved_path))
            player.stop()
            player.set_media(media)

            current_file = relative_path
            result = player.play()

    if result == -1:
        return jsonify({"error": "VLC could not start playback"}), 500

    return jsonify({"message": "Playback started", "file": current_file})


@app.route("/pause", methods=["POST"])
def pause():

    with player_lock:
        player.set_pause(1)

    return jsonify({"message": "Paused"})


@app.route("/resume", methods=["POST"])
def resume():

    with player_lock:
        player.set_pause(0)

    return jsonify({"message": "Resumed"})


@app.route("/stop", methods=["POST"])
def stop():

    global current_file

    with player_lock:
        player.stop()
        current_file = None

    return jsonify({"message": "Stopped"})


@app.route("/volume", methods=["POST"])
def volume():

    data = request.get_json(silent=True) or {}

    try:
        value = max(0, min(100, int(data["value"])))
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Provide a volume value from 0 to 100"}), 400

    with player_lock:
        player.audio_set_volume(value)

    return jsonify({"volume": value})


@app.route("/seek", methods=["POST"])
def seek():

    data = request.get_json(silent=True) or {}

    try:
        seconds = max(0, float(data["seconds"]))
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Provide a valid position in seconds"}), 400

    with player_lock:
        player.set_time(int(seconds * 1000))

    return jsonify({"position_seconds": seconds})


if __name__ == "__main__":

    mode = sys.argv[1] if len(sys.argv) > 1 else "http"

    print("Musibile VLC Receiver API")
    print(f"Listening on port 5002 ({mode.upper()})")

    if mode == "https":
        app.run(
            host="0.0.0.0",
            port=5002,
            threaded=True,
            use_reloader=False,
            ssl_context=("cert.pem", "key.pem"),
        )
    else:
        app.run(host="0.0.0.0", port=5002, threaded=True, use_reloader=False)
