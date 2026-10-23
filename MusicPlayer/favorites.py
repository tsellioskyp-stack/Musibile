import json
import sqlite3
import os
import tempfile
import sys

from threading import Lock

from flask import Flask, request, jsonify
from flask_cors import CORS

# Configuration

if len(sys.argv) != 2:
    sys.exit(
        "Usage: python favorites_api.py [Path to music library where all the albums, .json file and databse are stored (C://Users/Music)]"
    )
if not os.path.isdir(sys.argv[1]):
    sys.exit("Path to music library does not exist!")
else:
    BASE_DIR = os.path.abspath(sys.argv[1])
    JSON_PATH = os.path.join(BASE_DIR, "music.json")
    DB_PATH = os.path.join(BASE_DIR, "library.db")

app = Flask(__name__)
CORS(app)

# Prevent simultaneous requests from overwriting each other.
favorites_lock = Lock()


# --------------------------------------------------
# Update favorite status
# --------------------------------------------------


@app.route("/api/favorites", methods=["POST"])
def update_favorite():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON request"}), 400

    file_path = data.get("file")
    favorite = data.get("favorite")

    if not isinstance(file_path, str) or not file_path:
        return jsonify({"error": "Missing track file path"}), 400

    if not isinstance(favorite, bool):
        return jsonify({"error": "favorite must be true or false"}), 400

    with favorites_lock:
        # Read the master JSON file.
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as music:
                tracks = json.load(music)
        except (OSError, json.JSONDecodeError):
            app.logger.exception("Could not read music.json")
            return jsonify({"error": "Could not read music.json"}), 500

        # Find the track using its relative file path.
        track = next((t for t in tracks if t.get("file") == file_path), None)

        if track is None:
            return jsonify({"error": "Track not found"}), 404

        # Avoid rewriting files when nothing has changed.
        if track.get("favorite", False) == favorite:
            return jsonify(
                {
                    "success": True,
                    "file": file_path,
                    "favorite": favorite,
                    "unchanged": True,
                }
            )

        # Update the master JSON first.
        track["favorite"] = favorite

        temp_path = None

        try:
            fd, temp_path = tempfile.mkstemp(dir=BASE_DIR, suffix=".tmp")

            with os.fdopen(fd, "w", encoding="utf-8") as music:
                json.dump(tracks, music, indent=4, ensure_ascii=False)
                music.write("\n")

            # Atomically replace the master file.
            os.replace(temp_path, JSON_PATH)
            temp_path = None

        except OSError:
            app.logger.exception("Could not update music.json")
            return jsonify({"error": "Could not save music.json"}), 500

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        # Sync SQLite with the updated master.
        try:
            with sqlite3.connect(DB_PATH) as db:
                cursor = db.execute(
                    "UPDATE tracks SET favorite = ? WHERE file = ?",
                    (int(favorite), file_path),
                )

                if cursor.rowcount == 0:
                    app.logger.error(
                        "Track exists in JSON but not in SQLite: %s", file_path
                    )
                    return (
                        jsonify(
                            {"error": "JSON updated, but SQLite track was not found"}
                        ),
                        500,
                    )

        except sqlite3.Error:
            app.logger.exception("Could not update SQLite")
            return (
                jsonify({"error": "JSON updated, but SQLite synchronization failed"}),
                500,
            )

    return jsonify({"success": True, "file": file_path, "favorite": favorite})


# Start API server

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
