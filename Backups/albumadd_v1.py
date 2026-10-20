import os
import sys
import json
import mutagen

if len(sys.argv) == 1:
    sys.exit(
        'Usage: python albumadd_v1.py "root\\...\\Music Library Folder" "root\\subfolder\\added_album1" "root\\subfolder\\added_album2" ... The Music Library Folder comes first, then the directories of the added albums!!'
    )
if os.path.exists(sys.argv[1]):
    music_folder = sys.argv[1]
    project_folder = os.path.dirname(music_folder)
else:
    sys.exit("Error: Library folder not found")
json_path = os.path.join(music_folder, "music.json")
existing_songs_paths_path = os.path.join(music_folder, "existing_songs_paths.txt")


def cleanup_paths(paths: list):

    # Check if provided paths exist
    # and create a list containing only valid paths, then return it. If any invalid paths are found, print them to the terminal and ask the user if they want to continue or exit the program.

    cleaned_paths = []
    invalid_paths = []

    for path in paths:
        if os.path.exists(path):
            # Search within the provided path for subdirectories, and in that case, branch out and add those subdirectories to the cleaned_paths list instead of the provided path.

            for root, dirs, files in os.walk(path):
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    if os.path.exists(dir_path):
                        cleaned_paths.append(dir_path)

        else:

            print(f"Path {path} does not exist")
            invalid_paths.append(path)

    # output to the terminal the valid and invalid paths, and ask the user if they want to continue
    print(f"Valid paths to scan: {len(cleaned_paths)}")
    for path in cleaned_paths:
        print(f"  - {path}")

    if invalid_paths:
        print(f"Invalid paths: {len(invalid_paths)}")
        for path in invalid_paths:
            print(f"  - {path}")
    if cleaned_paths and input("Do you want to continue? (y/n): ").lower() != "y":
        sys.exit("Exiting program.")
    return cleaned_paths


def metadata(paths: list):

    songs = []

    for path in paths:

        for root, dirs, files in os.walk(path):

            for file in files:

                if file.lower().endswith((".flac", ".mp3", ".m4a", ".opus")):

                    full_path = os.path.join(root, file)
                    dir_path = os.path.dirname(full_path)

                    # Read audio metadata
                    audio = mutagen.File(full_path)

                    if audio is None:
                        continue

                    # Album name
                    album = audio.get("album", [None])[0]

                    # Extract embedded cover image
                    cover_file = None

                    if album:

                        cover_file = os.path.join(dir_path, album + ".jpg")

                    # Album exists, but cover has not been
                    # created as a file yet
                    if cover_file is not None and not os.path.exists(cover_file):

                        for picture in audio.pictures:

                            if picture.type == 3:  # 3 = front cover

                                with open(cover_file, "wb") as f:
                                    f.write(picture.data)

                                break

                    # Pull metadata from the audio file

                    relative_cover = (
                        "/"
                        + os.path.relpath(cover_file, project_folder).replace("\\", "/")
                        if cover_file
                        else None
                    )
                    relative_file = "/" + os.path.relpath(
                        full_path, project_folder
                    ).replace("\\", "/")

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
                            "size": os.path.getsize(full_path),
                        }
                    )

    # Update already existing music.json

    try:

        with open(json_path, "r", encoding="utf-8") as f:
            music_data = json.load(f)

    except FileNotFoundError:

        music_data = []

    # Add newly discovered songs
    music_data.extend(songs)

    # Write updated music.json
    with open(json_path, "w", encoding="utf-8") as f:

        json.dump(music_data, f, indent=4, ensure_ascii=False)

    # Append newly discovered album directories to existing_songs_paths.txt, avoiding duplicates

    try:
        with open(existing_songs_paths_path, "r", encoding="utf-8") as f:
            existing_paths = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        existing_paths = set()

    for path in paths:
        if path not in existing_paths:
            existing_paths.add(path)

    with open(existing_songs_paths_path, "w", encoding="utf-8") as f:
        for path in sorted(existing_paths):
            f.write(path + "\n")

    print(f"Songs added: {len(songs)}")


# Main program


paths = cleanup_paths(sys.argv[2:])

metadata(paths)


# Known bugs: It will add a duplicate .json insert if an existing track is re-added. This is because the program does not check for duplicates in the .json file, only in the existing_songs_paths.txt file. A future update will include a check for duplicates in the .json file before adding new entries.

# Also, this script cannot understand if the provided sys.argv argument of a path of an added album is actually an album path, containing music files, or more folders within. The problem is in the re-writing of the existing_songs_path.txt file. For example, if the user provides a path to a folder that contains multiple albums, the script will add that path to the existing_songs_paths.txt file, but it will not add the individual album paths within that folder. This is because the script only adds the provided paths to the existing_songs_paths.txt file, and does not check for subfolders within those paths. A future update will include a check for subfolders within the provided paths, and will add those subfolder paths to the existing_songs_paths.txt file as well.
