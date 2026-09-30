import os
import json
import re
import mutagen

# ============================================================
# FUNCTIONS
# ============================================================

music_folder = r"C:\Users\mitsu\Musibile\MusicPlayer\songs"
existing_songs_paths = set()
# Main MusicPlayer project directory
project_folder = os.path.dirname(music_folder)


def safe_filename(name):
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


# ============================================================
# SCAN MUSIC
# ============================================================
# ============================================================
# SETTINGS
# ============================================================


def main():

    songs = []

    for root, dirs, files in os.walk(music_folder):

        for file in files:

            if not file.lower().endswith((".flac", ".mp3", ".m4a")):
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


if __name__ == "__main__":
    main()
