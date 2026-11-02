import sqlite3, json, sys, os

if len(sys.argv) != 2:
    sys.exit(
        "Usage: python setupdb.py [Path to music library where all the albums and .json files are, and where the database will be stored (e.g.: python setupdb.py 'C:/Users/Music')"
    )
if not os.path.isdir(sys.argv[1]):
    sys.exit("Path to music library does not exist!")
else:
    lib_path = sys.argv[1]
    db_path = os.path.join(lib_path, "library.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create a music library db, if not already existing:
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            track_number INTEGER,
            title TEXT,
            artist TEXT,
            albumartist TEXT,
            album TEXT,
            year INTEGER,
            genre TEXT,
            cover TEXT,
            file TEXT UNIQUE,
            size_MB REAL,
            bitrate_kbps REAL,
            sample_rate_khz REAL,
            bit_depth INTEGER,
            length_sec REAL,
            file_type TEXT,
            favorite INTEGER DEFAULT 0
        )
    """)

    try:
        with open(os.path.join(lib_path, "music.json"), "r", encoding="utf-8") as music:
            tracks = json.load(music)
        for track in tracks:
            cursor.execute(
                """
                    INSERT OR IGNORE INTO tracks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        track["track_number"]
                        if track["track_number"] is not None
                        else None
                    ),
                    track["title"] if track["title"] is not None else None,
                    track["artist"] if track["artist"] is not None else None,
                    track["albumartist"] if track["albumartist"] is not None else None,
                    track["album"] if track["album"] is not None else None,
                    int(track["year"]) if track["year"] is not None else None,
                    track["genre"] if track["genre"] is not None else None,
                    track["cover"] if track["cover"] is not None else None,
                    track["file"] if track["file"] is not None else None,
                    (
                        float(track["size"].replace(" MB", ""))
                        if track["size"] is not None
                        else None
                    ),
                    (
                        float(track["bitrate"].replace("kbps", ""))
                        if track["bitrate"] is not None
                        else None
                    ),
                    (
                        float(track["sample_rate"].replace("kHz", ""))
                        if track["sample_rate"] is not None
                        else None
                    ),
                    (
                        int(track["bit_depth"].replace("-bit", ""))
                        if track["bit_depth"] is not None
                        else None
                    ),
                    (
                        float(track["length"].replace("s", ""))
                        if track["length"] is not None
                        else None
                    ),
                    track["file_type"] if track["file_type"] is not None else None,
                    track["favorite"],
                ),
            )
    except FileNotFoundError:
        sys.exit("No .json file found in the music library directory!")
    conn.commit()
finally:
    conn.close()
    print(f"Your database was successfully created in: {lib_path} ")
