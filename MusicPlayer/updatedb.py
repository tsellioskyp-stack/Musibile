"""Script used to UPDATE (INSERT) newly added albums into the library database, by parsing the updates.json"""

import sqlite3, json, sys, os

# Terminal Usage: python updatedb.py "Directory of the library.db"
### ERROR CHECKING IN TERMINAL #######################################################################

if len(sys.argv) != 2:
    sys.exit(
        "Usage: python updatedb.py [Directory to music library where all the albums and .json files are, and where the database is stored (e.g. If the library.db is 'C:/Users/Music/library.db', use: python updatedb.py 'C:/Users/Music')"
    )
if not os.path.isdir(sys.argv[1]):
    sys.exit("Path to music library does not exist! / Invalid Path !")
else:
    LIBRARY_PATH = sys.argv[1]
    DB_PATH = (
        os.path.join(LIBRARY_PATH, "library.db")
        if os.path.exists(os.path.join(LIBRARY_PATH, "library.db"))
        else sys.exit("No library database found!")
    )
    UPDATE_JSON_PATH = (
        os.path.join(LIBRARY_PATH, "updates.json")
        if os.path.exists(os.path.join(LIBRARY_PATH, "updates.json"))
        else sys.exit("No updates.json found!")
    )

############################################################################################################

### CONNECT TO THE library.db DATABASE ###################################################################
try:
    conn = sqlite3.connect(DB_PATH)
except sqlite3.Error as e:
    sys.exit(f"Database error: {e}")
cursor = conn.cursor()
############################################################################################################

### INSERT into DB ###################################################################

inserted = []
ignored = []
with open(UPDATE_JSON_PATH, "r", encoding="utf-8") as updates:
    tracks = json.load(updates)
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
        (
            ignored.append(track["file"])
            if cursor.rowcount == 0
            else inserted.append(track["file"])
        )

conn.commit()
conn.close()
os.remove(UPDATE_JSON_PATH)
print(
    f"\n{"=" * os.get_terminal_size().columns}\nYour database was successfully updated! All the scheduled album updates in updates.json were commited, and the updates.json was deleted!\n{"=" * os.get_terminal_size().columns}\n"
)
print(f"Tracks added to the database: \n")
for i in inserted:
    print(i)
print(f"Tracks that were duplicates in the database (ignored): \n")
for i in ignored:
    print(f"\t{i}")
