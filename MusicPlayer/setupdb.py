import sqlite3, json, sys, os

if len(sys.argv) != 2:
    sys.exit("Usage: python setupdb.py [Path to music library/Albums/Track...]")
if not os.path.exists(sys.argv[1]):
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
                    INSERT OR IGNORE INTO tracks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    track["title"],
                    track["artist"],
                    track["albumartist"],
                    track["album"],
                    int(track["year"]) if track["year"] is not None else None,
                    track["genre"],
                    track["cover"],
                    track["file"],
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
                        float(track["length"].replace("s", ""))
                        if track["length"] is not None
                        else None
                    ),
                    track["file_type"],
                    track["favorite"],
                ),
            )
    except FileNotFoundError:
        sys.exit("No .json file found in the music library directory!")
    conn.commit()
finally:
    conn.close()
    print(f"Your database was successfully created in: {lib_path} ")
