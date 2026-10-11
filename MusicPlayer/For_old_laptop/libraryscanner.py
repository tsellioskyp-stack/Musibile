import os
import json
import re
import sys
import mutagen
import argparse
import shutil
import time


def safe_filename(name: str) -> str:
    """
    Convert a string into a Windows-safe filename.
    """

    if not name:
        return "Unknown Album"

    # Characters that Windows does not allow in filenames
    name = re.sub(r'[<>:"/\\|?*]', "_", name)

    # Windows does not like filenames ending in a space or dot
    name = name.rstrip(" .")

    return name


def get_tag(audio, tag):
    """
    Safely get the first value of a Mutagen tag.
    """

    value = audio.get(tag)

    if value:
        return value[0]

    return None


def check_for_embedded_cover_images(music_folder: str) -> None:
    no_picture_file = []
    for root, dirs, files in os.walk(music_folder):

        for file in files:

            if not file.lower().endswith((".flac", ".mp3", ".m4a", ".opus")):
                continue

            path = os.path.join(root, file)

            try:
                audio = mutagen.File(path)

                pictures = audio.pictures

                if pictures:
                    print("✓ HAS IMAGE:", path)
                else:
                    print("✗ NO IMAGE: ", path)
                    no_picture_file.append(path)

            except Exception as e:
                print("ERROR:", path)
                print(e)

    if no_picture_file:
        print("\n\nFiles without embedded images:")
        for file in no_picture_file:
            print(file)


def scan_library(music_folder: str) -> None:
    existing_songs_paths = set()
    # Main MusicPlayer project directory
    project_folder = os.path.dirname(music_folder)

    songs = []

    for root, dirs, files in os.walk(music_folder):

        for file in files:

            if not file.lower().endswith((".flac", ".mp3", ".m4a", ".opus")):
                continue

            full_path = os.path.join(root, file)
            dir_path = os.path.dirname(
                full_path
            )  # Create a set of existing song paths (album directories) to avoid duplicates
            (
                existing_songs_paths.add(dir_path)
                if dir_path not in existing_songs_paths
                else None
            )

            print(f"Scanning: {full_path}")

            try:
                # Read file metadata
                audio = mutagen.File(full_path)

                if audio is None:
                    print("  ERROR: Could not read file")
                    continue

            except Exception as e:
                print(f"  ERROR reading file: {e}")
                continue

            # METADATA

            title = get_tag(audio, "title")
            artist = get_tag(audio, "artist")
            albumartist = get_tag(audio, "albumartist")
            album = get_tag(audio, "album")
            year = get_tag(audio, "date")

            genres = audio.get("genre", [])

            if genres:
                genre = ", ".join(genres)
            else:
                genre = ""

            # COVER ART

            cover_file = None

            if album:

                # Make album name safe for Windows
                safe_album = safe_filename(album)

                cover_file = os.path.join(dir_path, safe_album + ".jpg")

            # Look for embedded pictures
            pictures = getattr(audio, "pictures", [])

            if pictures:

                front_cover = None

                # First look specifically for FRONT COVER
                for picture in pictures:

                    if picture.type == 3:
                        front_cover = picture
                        break

                # If there is no type 3 image,
                # use the first embedded image
                if front_cover is None:
                    front_cover = pictures[0]

                if cover_file:

                    try:

                        # Only create the image if it doesn't already exist
                        if not os.path.exists(cover_file):

                            with open(cover_file, "wb") as f:
                                f.write(front_cover.data)

                            print(
                                f"  ✓ Cover created: " f"{os.path.basename(cover_file)}"
                            )

                        else:

                            print(
                                f"  ✓ Cover already exists: "
                                f"{os.path.basename(cover_file)}"
                            )

                    except Exception as e:

                        print(f"  ERROR writing cover: {e}")

            else:

                print("  - No embedded artwork")

            # WEB PATHS

            relative_file = "/" + os.path.relpath(full_path, project_folder).replace(
                "\\", "/"
            )

            if cover_file and os.path.exists(cover_file):

                relative_cover = "/" + os.path.relpath(
                    cover_file, project_folder
                ).replace("\\", "/")

            else:

                relative_cover = None

            # STORE SONG

            songs.append(
                {
                    "title": title,
                    "artist": artist,
                    "albumartist": albumartist,
                    "album": album,
                    "year": year,
                    "genre": genre,
                    "cover": relative_cover,
                    "file": relative_file,
                    "size": os.path.getsize(full_path),
                }
            )

    # GENERATE music.json and existing_songs_paths.txt

    json_path = os.path.join(music_folder, "music.json")
    existing_songs_paths_path = os.path.join(music_folder, "existing_songs_paths.txt")

    with open(json_path, "w", encoding="utf-8") as f:

        json.dump(songs, f, indent=4, ensure_ascii=False)

    with open(existing_songs_paths_path, "w", encoding="utf-8") as f:

        for path in sorted(existing_songs_paths):
            f.write(path + "\n")

    # ============================================================
    # RESULT
    # ============================================================

    print()
    print("=" * 60)
    print("Music library generated successfully!")
    print("=" * 60)
    print(f"JSON: {json_path}")
    print(f"Existing songs paths .txt file output at: {existing_songs_paths_path}")
    print(f"Songs found: {len(songs)}")


def update_library(music_folder: str, valid_folders: list) -> None:
    project_folder = os.path.dirname(music_folder)
    json_path = os.path.join(music_folder, "music.json")
    existing_songs_paths_path = os.path.join(music_folder, "existing_songs_paths.txt")
    songs = []

    for folder in valid_folders:

        for root, dirs, files in os.walk(folder):

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

    for folder in valid_folders:
        for root, dirs, files in os.walk(folder):
            for filename in files:
                if filename.endswith((".mp3", ".flac", ".wav")):
                    full_path = os.path.join(root, filename)
                    existing_paths.add(full_path)

    with open(existing_songs_paths_path, "w", encoding="utf-8") as f:
        for path in sorted(existing_paths):
            f.write(path + "\n")

    print(f"Songs added: {len(songs)}")


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    terminal_width = shutil.get_terminal_size().columns

    parser = argparse.ArgumentParser()
    # Optional cover argument
    parser.add_argument(
        "-c",
        "--cover",
        action="store_true",
        help="Optionally scan and extract embedded album covers (scan mode only)",
    )
    # Only one mode can be selected, between scanning and updating the library
    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument(
        "-s",
        "--scan",
        action="store_true",
        help="Scan the music library and generate music.json and existing_songs_paths.txt",
    )

    mode.add_argument(
        "-u",
        "--update",
        nargs="+",
        metavar="NEW_FOLDER",
        help="Update the music library using one or more new music folders",
    )

    parser.add_argument(
        "music_folder",
        type=str,
        help="Path to the root music library folder",
    )

    args = parser.parse_args()

    # ======================================================================================================================
    # ERROR HANDLING
    # ======================================================================================================================

    # Check the root music folder
    music_folder = args.music_folder

    if not os.path.isdir(music_folder):
        sys.exit(f"Error: Root music folder not found: {music_folder}")

    # Check the new music folders, if updating or checking for embedded cover images
    invalid_update_folders = []
    valid_update_folders = []
    invalid_cover_folders = []
    valid_cover_folders = []
    if args.update:
        for folder in args.update:
            if not os.path.isdir(folder):
                print(f"Error: Directory not found: {folder}")
                invalid_update_folders.append(folder)
            else:
                valid_update_folders.append(folder)
    if args.cover:
        if not args.scan:
            parser.error("-c/--cover can only be used with -s/--scan")
        if not os.path.isdir(music_folder):
            print(f"Error: Directory not found: {music_folder}")
            invalid_cover_folders.append(music_folder)
        else:
            valid_cover_folders.append(music_folder)

    # ======================================================================================================================
    # NORMAL OPERATIONS
    # ======================================================================================================================

    # CHECK FOR EMBEDDED COVER IMAGES MODE. This mode is independent of scanning or updating the library, and can be run on any folder containing music files.

    if args.cover:
        print("=" * terminal_width)
        print(f"Checking for embedded cover images in: {music_folder}")
        print("=" * terminal_width)

        time.sleep(2)

        check_for_embedded_cover_images(music_folder)

    # SCANNING MODE

    if args.scan:
        print("=" * terminal_width)
        print(f"Scanning music library at: {music_folder}")
        print("=" * terminal_width)

        time.sleep(2)

        scan_library(music_folder)

    # UPDATE MODE

    elif args.update:
        print("=" * terminal_width)
        print(f"Updating music library at: {music_folder}")
        print("=" * terminal_width)

        if valid_update_folders:
            print("Valid directories to add:")
            for folder in valid_update_folders:
                for root, dirs, files in os.walk(folder):
                    if not dirs:
                        print(f"  {root}")
        (print("Invalid Directories:") if invalid_update_folders else None)
        for folder in invalid_update_folders:
            print(f"  {folder}")
        if valid_update_folders:
            print(
                "Continue with the update ? (Invalid directories will be skipped) (y/n): ",
                end="",
            )
            while True:
                user_input = input().strip().lower()
                if user_input in ["y", "n"]:
                    break
                print("Invalid input. Please enter 'y' or 'n': ", end="")
            if user_input == "n":
                sys.exit("Update cancelled by user.")

            time.sleep(2)

            update_library(music_folder, valid_update_folders)


if __name__ == "__main__":
    main()
