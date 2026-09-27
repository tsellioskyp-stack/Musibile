import os
import json
import mutagen

# Your songs directory
music_folder = r"C:\Users\mitsu\Musibile\MusicPlayer\songs"

# The main MusicPlayer project directory
project_folder = os.path.dirname(music_folder)

last_picture = None
parsed = []
songs = []


for root, dirs, files in os.walk(music_folder):

    for file in files:

        if file.lower().endswith(".flac"):

            # Full path to the FLAC file
            full_path = os.path.join(root, file)

            # Directory containing the FLAC
            dir_path = os.path.dirname(full_path)

            # Read FLAC metadata
            audio = mutagen.File(full_path)

            if audio is None:
                continue

            # Album name
            album = audio.get("album", [None])[0]

            # Extract embedded cover image

            cover_file = None

            if album:

                cover_file = os.path.join(dir_path, album + ".jpg")

                for picture in audio.pictures:

                    if picture.type == 3:  # 3 = front cover

                        if picture.data not in parsed:

                            with open(cover_file, "wb") as f:
                                f.write(picture.data)

                            parsed.append(picture.data)

                        break

            # Create WEB paths

            # Path relative to MusicPlayer/
            relative_file = os.path.relpath(full_path, project_folder).replace(
                "\\", "/"
            )

            if cover_file and os.path.exists(cover_file):

                relative_cover = os.path.relpath(cover_file, project_folder).replace(
                    "\\", "/"
                )

            else:

                relative_cover = None

            # -------------------------------------------------
            # Store metadata
            # -------------------------------------------------

            songs.append(
                {
                    "title": audio.get("title", [None])[0],
                    "artist": audio.get("artist", [None])[0],
                    "albumartist": audio.get("albumartist", [None])[0],
                    "album": audio.get("album", [None])[0],
                    "year": audio.get("date", [None])[0],
                    "genre": ", ".join(audio.get("genre", [])),
                    "cover": relative_cover,
                    "file": relative_file,
                }
            )


# Generate music.json in the MusicPlayer project folder

json_path = os.path.join(music_folder, "music.json")

with open(json_path, "w", encoding="utf-8") as f:

    json.dump(songs, f, indent=4, ensure_ascii=False)

print(f"Created {json_path}")
print(f"Songs found: {len(songs)}")
