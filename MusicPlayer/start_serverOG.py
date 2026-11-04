import subprocess
import sys
from pathlib import Path
import time
import argparse

BASE_DIR = Path(__file__).resolve().parent
FAVORITES_API_SCRIPT = BASE_DIR / "favorites.py"
PLAYLIST_API_SCRIPT = BASE_DIR / "playlists_api.py"

parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument(
    "--http",
    action="store_true",
    help="Launch an HTTP server (for the APIs too)",
)

mode.add_argument(
    "--https",
    action="store_true",
    help="Launch an HTTPS server (for the APIs too)",
)

# Music library / database path
parser.add_argument(
    "library_path",
    help="Path to the music library/database ('C:/....')",
)
args = parser.parse_args()

LIBRARY_DIR = Path(args.library_path).resolve()

if not LIBRARY_DIR.is_dir():
    sys.exit(
        f"Error: Music library directory / Music Library DB directory does not exist: {LIBRARY_DIR}"
    )

processes = []
if args.http:
    try:
        print("Starting Musibile servers...")
        # Start the HTTP server
        http_server = subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "http-server . -p 8080 -c-1",
            ],
            cwd=BASE_DIR,
        )
        processes.append(http_server)

        # Start the favorites API using this venv's Python
        favorites = subprocess.Popen(
            [
                sys.executable,
                str(FAVORITES_API_SCRIPT),
                str(LIBRARY_DIR),
                "http",
            ],
            cwd=BASE_DIR,
        )
        processes.append(favorites)

        # Start the playlists API using this venv's Python
        playlists = subprocess.Popen(
            [
                sys.executable,
                str(PLAYLIST_API_SCRIPT),
                str(LIBRARY_DIR),
                "http",
            ],
            cwd=BASE_DIR,
        )
        processes.append(playlists)

        print("HTML player: http://localhost:8080")
        print("Favorites API: http://localhost:5000")
        print("Playlists API: http://localhost:5001")
        print("Press Ctrl+C to stop both servers.")

        # Keep the launcher alive while both servers run
        while True:
            for process in processes:
                if process.poll() is not None:
                    raise RuntimeError(
                        f"A server stopped unexpectedly "
                        f"(exit code {process.returncode})."
                    )
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping Musibile servers...")

    except RuntimeError as error:
        print(error)

    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()

        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        print("Musibile servers stopped.")
if args.https:
    try:
        print("Starting Musibile servers...")
        # Start the HTTP server
        http_server = subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "http-server -S -C 'cert.pem' -K 'key.pem' -p 8080",
            ],
            cwd=BASE_DIR,
        )
        processes.append(http_server)

        # Start the favorites API using this venv's Python
        favorites = subprocess.Popen(
            [
                sys.executable,
                str(FAVORITES_API_SCRIPT),
                str(LIBRARY_DIR),
                "https",
            ],
            cwd=BASE_DIR,
        )
        processes.append(favorites)

        # Start the playlists API using this venv's Python
        playlists = subprocess.Popen(
            [
                sys.executable,
                str(PLAYLIST_API_SCRIPT),
                str(LIBRARY_DIR),
                "https",
            ],
            cwd=BASE_DIR,
        )
        processes.append(playlists)

        print("HTML player: http://localhost:8080")
        print("Favorites API: http://localhost:5000")
        print("Playlists API: http://localhost:5001")
        print("Press Ctrl+C to stop both servers.")

        # Keep the launcher alive while both servers run
        while True:
            for process in processes:
                if process.poll() is not None:
                    raise RuntimeError(
                        f"A server stopped unexpectedly "
                        f"(exit code {process.returncode})."
                    )
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping Musibile servers...")

    except RuntimeError as error:
        print(error)

    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()

        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        print("Musibile servers stopped.")
