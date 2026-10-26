"""Flask API for Musibile playlists.

Set MUSIBILE_DB_PATH to the full path of library.db if it is not in the
same directory as this script. This API intentionally does not create a new
SQLite database when library.db is missing.
"""

import os
import re
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = (
    Path(
        os.environ.get(
            "MUSIBILE_DB_PATH", Path(__file__).resolve().with_name("library.db")
        )
    )
    .expanduser()
    .resolve()
)

PLAYLIST_NAME_RE = re.compile(r"^[\w -]{1,64}$", re.UNICODE)


class LibraryDatabaseMissing(Exception):
    pass


def get_connection():
    """Open the existing library database without silently creating one."""
    if not DB_PATH.is_file():
        raise LibraryDatabaseMissing(
            f"Library database was not found: {DB_PATH}. "
            "Set MUSIBILE_DB_PATH to the location of your existing library.db."
        )

    connection = sqlite3.connect(DB_PATH, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def db_connection():
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def ensure_playlist_registry(connection):
    """Create the playlist-name registry if it does not already exist."""
    connection.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            name TEXT PRIMARY KEY COLLATE NOCASE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)


def validate_name(value):
    if not isinstance(value, str):
        return None
    name = value.strip()
    if not name or len(name) > 64 or not PLAYLIST_NAME_RE.fullmatch(name):
        return None
    return name


def table_exists(connection, name):
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? COLLATE NOCASE",
        (name,),
    ).fetchone()
    return row is not None


def json_error(message, status):
    return jsonify(success=False, error=message), status


@app.after_request
def add_cors_headers(response):
    # The player is commonly served from a different local port than Flask.
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    return response


@app.get("/api/playlists")
def list_playlists():
    try:
        with db_connection() as connection:
            ensure_playlist_registry(connection)
            rows = connection.execute(
                "SELECT name FROM playlists ORDER BY name COLLATE NOCASE"
            ).fetchall()
            return jsonify(success=True, playlists=[row["name"] for row in rows])
    except LibraryDatabaseMissing as error:
        return json_error(str(error), 503)
    except sqlite3.Error as error:
        app.logger.exception("Could not list playlists")
        return json_error(f"Could not read playlists: {error}", 500)


@app.get("/api/playlists/check")
def check_playlist_name():
    name = validate_name(request.args.get("name", ""))
    if name is None:
        return json_error(
            "Use 1–64 letters, numbers, spaces, underscores or hyphens.", 400
        )

    try:
        with db_connection() as connection:
            ensure_playlist_registry(connection)
            exists = table_exists(connection, name)
            return jsonify(success=True, name=name, exists=exists)
    except LibraryDatabaseMissing as error:
        return json_error(str(error), 503)
    except sqlite3.Error as error:
        app.logger.exception("Could not check playlist name")
        return json_error(f"Could not check playlist name: {error}", 500)


@app.route("/api/playlists/delete", methods=["POST", "OPTIONS"])
def delete_playlist():
    if request.method == "OPTIONS":
        return "", 204
    payload = request.get_json(silent=True) or {}
    name = validate_name(payload.get("name"))

    if name is None:
        return json_error("Invalid playlist name.", 400)

    try:
        with db_connection() as connection:
            row = connection.execute(
                "SELECT name FROM playlists WHERE name = ? COLLATE NOCASE",
                (name,),
            ).fetchone()

            if row is None:
                return json_error("Playlist not found.", 404)

            # Use the actual registered name and safely quote the table identifier.
            name = row["name"]
            quoted_name = '"' + name.replace('"', '""') + '"'

            if table_exists(connection, name):
                connection.execute(f"DROP TABLE {quoted_name}")

            connection.execute(
                "DELETE FROM playlists WHERE name = ? COLLATE NOCASE",
                (name,),
            )

            return jsonify(success=True, name=name)

    except LibraryDatabaseMissing as error:
        return json_error(str(error), 503)
    except sqlite3.Error as error:
        app.logger.exception("Could not delete playlist")
        return json_error(f"Could not delete playlist: {error}", 500)


@app.post("/api/playlists/create")
def create_playlist():
    payload = request.get_json(silent=True) or {}
    name = validate_name(payload.get("name"))
    if name is None:
        return json_error(
            "Use 1–64 letters, numbers, spaces, underscores or hyphens.", 400
        )

    try:
        with db_connection() as connection:
            ensure_playlist_registry(connection)

            # Check all tables, not just registry entries, so an existing table
            # with this name is never accidentally reused or overwritten.
            if table_exists(connection, name):
                return json_error(
                    f'A playlist or table named "{name}" already exists.', 409
                )

            # The table name is quoted as an SQLite identifier. Validation above
            # disallows quotes and SQL punctuation in names.
            quoted_name = '"' + name.replace('"', '""') + '"'
            connection.execute(
                f"CREATE TABLE {quoted_name} ("
                "song_file TEXT PRIMARY KEY, "
                "position INTEGER NOT NULL, "
                "added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"
                ")"
            )
            connection.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
            connection.commit()
            return jsonify(success=True, name=name), 201
    except LibraryDatabaseMissing as error:
        return json_error(str(error), 503)
    except sqlite3.Error as error:
        app.logger.exception("Could not create playlist")
        return json_error(f"Could not create playlist: {error}", 500)


@app.route("/api/playlists/add", methods=["POST"])
def add_track_to_playlist():
    payload = request.get_json(silent=True) or {}

    name = validate_name(payload.get("name"))
    song_file = payload.get("file")

    if name is None:
        return json_error("Invalid playlist name.", 400)

    if not isinstance(song_file, str) or not song_file:
        return json_error("Missing track file.", 400)

    try:
        with db_connection() as connection:
            # Make sure the playlist actually exists.
            row = connection.execute(
                "SELECT name FROM playlists WHERE name = ? COLLATE NOCASE", (name,)
            ).fetchone()

            if row is None or not table_exists(connection, row["name"]):
                return json_error("Playlist not found.", 404)

            name = row["name"]
            quoted_name = '"' + name.replace('"', '""') + '"'

            # Prevent adding the same track twice.
            existing = connection.execute(
                f"SELECT 1 FROM {quoted_name} WHERE song_file = ?", (song_file,)
            ).fetchone()

            if existing:
                return json_error("Track is already in this playlist.", 409)

            # Place the track at the end of the playlist.
            connection.execute(
                f"""
                INSERT INTO {quoted_name} (song_file, position)
                VALUES (
                    ?,
                    (SELECT COALESCE(MAX(position), 0) + 1
                     FROM {quoted_name})
                )
                """,
                (song_file,),
            )

            return jsonify(success=True, playlist=name, file=song_file), 201

    except LibraryDatabaseMissing as error:
        return json_error(str(error), 503)
    except sqlite3.Error as error:
        app.logger.exception("Could not add track to playlist")
        return json_error(f"Could not add track: {error}", 500)


@app.get("/api/playlists/<name>/tracks")
def get_playlist_tracks(name):
    name = validate_name(name)

    if name is None:
        return json_error("Invalid playlist name.", 400)

    try:
        with db_connection() as connection:
            row = connection.execute(
                "SELECT name FROM playlists WHERE name = ? COLLATE NOCASE",
                (name,),
            ).fetchone()

            if row is None or not table_exists(connection, row["name"]):
                return json_error("Playlist not found.", 404)

            quoted_name = '"' + row["name"].replace('"', '""') + '"'

            tracks = connection.execute(f"""
                SELECT song_file, added_at
                FROM {quoted_name}
                ORDER BY added_at DESC, position DESC
                """).fetchall()

            return jsonify(
                success=True,
                playlist=row["name"],
                tracks=[
                    {
                        "file": track["song_file"],
                        "added_at": track["added_at"],
                    }
                    for track in tracks
                ],
            )

    except LibraryDatabaseMissing as error:
        return json_error(str(error), 503)
    except sqlite3.Error as error:
        app.logger.exception("Could not get playlist tracks")
        return json_error(f"Could not get playlist tracks: {error}", 500)


@app.route("/api/playlists/rename", methods=["POST", "OPTIONS"])
def rename_playlist():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}
    old_name = validate_name(payload.get("old_name"))
    new_name = validate_name(payload.get("new_name"))

    if old_name is None or new_name is None:
        return json_error("Invalid playlist name.", 400)

    try:
        with db_connection() as connection:
            ensure_playlist_registry(connection)

            row = connection.execute(
                "SELECT name FROM playlists WHERE name = ? COLLATE NOCASE",
                (old_name,),
            ).fetchone()

            if row is None:
                return json_error("Playlist not found.", 404)

            old_name = row["name"]

            if old_name.casefold() == new_name.casefold():
                return json_error("The new name must be different.", 400)

            exists = connection.execute(
                "SELECT 1 FROM playlists WHERE name = ? COLLATE NOCASE",
                (new_name,),
            ).fetchone()

            if exists or table_exists(connection, new_name):
                return json_error("A playlist with that name already exists.", 409)

            old_table = '"' + old_name.replace('"', '""') + '"'
            new_table = '"' + new_name.replace('"', '""') + '"'

            connection.execute(f"ALTER TABLE {old_table} RENAME TO {new_table}")

            connection.execute(
                "UPDATE playlists SET name = ? " "WHERE name = ? COLLATE NOCASE",
                (new_name, old_name),
            )

            return jsonify(
                success=True,
                old_name=old_name,
                name=new_name,
            )

    except LibraryDatabaseMissing as error:
        return json_error(str(error), 503)
    except sqlite3.Error as error:
        app.logger.exception("Could not rename playlist")
        return json_error(f"Could not rename playlist: {error}", 500)


@app.route("/api/playlists/duplicate", methods=["POST", "OPTIONS"])
def duplicate_playlist():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}
    source_name = validate_name(payload.get("name"))
    new_name = validate_name(payload.get("new_name"))

    if source_name is None or new_name is None:
        return json_error("Invalid playlist name.", 400)

    try:
        with db_connection() as connection:
            ensure_playlist_registry(connection)

            row = connection.execute(
                "SELECT name FROM playlists WHERE name = ? COLLATE NOCASE",
                (source_name,),
            ).fetchone()

            if row is None:
                return json_error("Playlist not found.", 404)

            source_name = row["name"]

            exists = connection.execute(
                "SELECT 1 FROM playlists WHERE name = ? COLLATE NOCASE",
                (new_name,),
            ).fetchone()

            if exists or table_exists(connection, new_name):
                return json_error("A playlist with that name already exists.", 409)

            source_table = '"' + source_name.replace('"', '""') + '"'
            new_table = '"' + new_name.replace('"', '""') + '"'

            connection.execute(
                f"CREATE TABLE {new_table} ("
                "song_file TEXT PRIMARY KEY, "
                "position INTEGER NOT NULL, "
                "added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )

            connection.execute(
                f"INSERT INTO {new_table} "
                "(song_file, position, added_at) "
                f"SELECT song_file, position, added_at "
                f"FROM {source_table}"
            )

            connection.execute(
                "INSERT INTO playlists (name) VALUES (?)",
                (new_name,),
            )

            return jsonify(success=True, name=new_name), 201

    except LibraryDatabaseMissing as error:
        return json_error(str(error), 503)
    except sqlite3.Error as error:
        app.logger.exception("Could not duplicate playlist")
        return json_error(f"Could not duplicate playlist: {error}", 500)


if __name__ == "__main__":
    # Optional argument may be the database file itself or its containing folder.
    if len(sys.argv) > 1:
        supplied_path = Path(sys.argv[1]).expanduser().resolve()
        DB_PATH = (
            supplied_path / "library.db" if supplied_path.is_dir() else supplied_path
        )

    print(f"Musibile playlists API using database: {DB_PATH}")
    app.run(host="0.0.0.0", port=5001, debug=False)
