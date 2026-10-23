import subprocess
import sys
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent
API_SCRIPT = BASE_DIR / "favorites.py"
LIBRARY_DIR = BASE_DIR / "songs"

processes = []

try:
    print("Starting Musibile servers...")

    # Start the static HTML server
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
            str(API_SCRIPT),
            str(LIBRARY_DIR),
        ],
        cwd=BASE_DIR,
    )
    processes.append(favorites)

    print("HTML player: http://localhost:8080")
    print("Favorites API: http://localhost:5000")
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
