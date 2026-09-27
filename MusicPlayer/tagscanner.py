import os
import json
import mutagen

music_folder = r"C:\Users\mitsu\C\MusicPlayer"
last_picture = None
parsed = []
i = 0

songs = []

for root, dirs, files in os.walk(music_folder):

    for file in files:

        if file.lower().endswith(".flac"):

            full_path = os.path.join(root, file)
            dir_path = os.path.dirname(full_path)

            relative_path = os.path.relpath(full_path, music_folder)

            audio = mutagen.File(full_path)
            cover_file = os.path.join(dir_path, audio.get("album", [None])[0] + ".jpg")
            cover_url = os.path.relpath(cover_file, music_folder).replace("\\", "/")

            # Exctract cover image from FLAC files

            for picture in audio.pictures:
                if picture.type == 3:  # 3 = front cover
                    if picture.data != last_picture and picture.data not in parsed:
                        cover_name = audio.get("album", [None])[0] + ".jpg"
                        with open(os.path.join(dir_path, cover_name), "wb") as f:
                            f.write(picture.data)
                        parsed.append(picture.data)
                        last_picture = picture.data
                        i += 1
                    else:
                        continue
            # Extract embedded metadata from FLAC files and store it in a list of dictionaries
            songs.append(
                {
                    "title": audio.get("title", [None])[0],
                    "artist": audio.get("artist", [None])[0],
                    "album": audio.get("album", [None])[0],
                    "genre": ", ".join(audio.get("genre", [None]))[0:],
                    "cover": cover_url if os.path.exists(cover_file) else None,
                    "file": relative_path.replace("\\", "/"),
                }
            )

with open("music.json", "w", encoding="utf-8") as f:
    json.dump(songs, f, indent=4, ensure_ascii=False)
