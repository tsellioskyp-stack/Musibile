```text
███╗   ███╗██╗   ██╗███████╗██╗██████╗ ██╗██╗     ███████╗
████╗ ████║██║   ██║██╔════╝██║██╔══██╗██║██║     ██╔════╝
██╔████╔██║██║   ██║███████╗██║██████╔╝██║██║     █████╗
██║╚██╔╝██║██║   ██║╚════██║██║██╔══██╗██║██║     ██╔══╝
██║ ╚═╝ ██║╚██████╔╝███████║██║██████╔╝██║███████╗███████╗
╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝╚═════╝ ╚═╝╚══════╝╚══════╝
```

## A self-hosted personal music library and web-based music player built for high-quality local music streaming.

Musibile is a personal music server project designed to make a large local music collection accessible through a custom web interface. It combines a lightweight web-based music player with Python-powered library management, allowing you to organize, browse, search, and play your music directly from your own computer.

Built with a focus on simplicity, customization, and self-hosting, Musibile is designed to handle a large music collection without relying on third-party streaming platforms or cloud music services.

## == Features ==

Custom web-based music player — A dark-themed interface with album artwork, playback controls, and a clean, responsive layout.

Music library browsing — Browse your collection by album artist, album, and individual tracks.

Search functionality — Search your library by track title, artist, album, and genre.

Album artwork — Display embedded album covers, with artwork extraction handled by the library scanner.

Playback controls — Play, pause, skip tracks, adjust volume, and seek through songs.

Shuffle and repeat — Control playback behavior with dedicated toggle options.

Animated album transitions — Cover animations and mobile swipe gestures for navigating between tracks.

Python-based metadata scanning — Extract track information such as title, artist, album artist, album, year, and genre.

Incremental library updates — Import specific album directories without rescanning the entire music collection.

Local music hosting — Serve your music library over a local network, with the possibility of remote access through a private network such as Tailscale.

Lossless audio support — Designed to work with formats such as FLAC, alongside MP3 and M4A files supported by the library scanner.

## == Technologies ==

HTML, CSS, and JavaScript — Frontend interface and playback logic.

Python — Music metadata scanning, artwork extraction, and album importing.

Mutagen — Reading audio metadata and embedded artwork.

JSON — Storing and exchanging music library metadata.

HTTP server — Hosting the web interface and music files.

Tailscale — Optional private-network connectivity for accessing the server remotely.

## == Library Management ==

Musibile includes Python scripts for scanning music directories and extracting metadata from supported audio files. The scanner collects information such as track titles, artists, albums, genres, and release years, while also extracting embedded front-cover artwork where available.

An incremental album-import workflow is intended to make library maintenance more efficient: instead of processing the entire collection every time, you can specify the album directories you want to add.

This approach is particularly useful for large libraries containing thousands of tracks.

## == Self-Hosting ==

The project is designed to run on your own computer, which acts as the music server. Other devices can access the web player through a browser over the same local network.

With an appropriately configured private network, such as Tailscale, the player can also be accessed remotely without making the music server publicly accessible to the entire internet.

## == Responsive Interface ==

The player is designed for desktop and mobile use, with a compact layout, album artwork animations, touch-based track navigation, and familiar playback controls.

## == Project Goals ==

Build a personal alternative to cloud-based music streaming.

Keep control of the music library and its storage.

Make large local music collections easier to browse and maintain.

Learn and apply Python, JavaScript, HTML, and CSS through a practical project.

Explore self-hosting, networking, metadata processing, and media delivery.

## == Project Status ==

Musibile is an ongoing personal project. Features, performance, and library-management workflows are being refined as the project develops.

## == Privacy and Ownership ==

Your music library remains on your own hardware. The project is intended for personal use, giving you control over your files, library organization, and access to your music.

Built as a personal project to combine music, programming, and self-hosted infrastructure.

# Library Scanner — Terminal Usage

`libraryscan.py` is the command-line library management script used by Musibile. It scans audio files, extracts metadata and album artwork, generates `music.json`, and supports incremental imports of new music folders.

## Requirements

- Python 3
- Mutagen, for reading audio metadata and embedded artwork
- An existing music library directory

Install the required dependency from your project's virtual environment:

```bash
pip install -r requirements.txt
```

## Command Syntax

Run the script from your terminal using the following syntax:

```bash
python libraryscan.py [OPTIONS] MUSIC_FOLDER
```

`MUSIC_FOLDER` is the root directory of your music library, such as `MusicPlayer/songs`.

The script supports two mutually exclusive operating modes: scanning and updating. An optional flag enables an embedded-artwork check during scanning.

## 1. Full Library Scan

Generate a new library database by scanning all supported audio files inside the specified music directory and its subdirectories.

**Command:**

```bash
python libraryscan.py --scan "C:\Users...\YourLIbraryOfMusic"
```

Short form:

```bash
python libraryscan.py -s "C:\Users...\YourLIbraryOfMusic"
```

### What it does

1. Recursively searches the music directory and its subdirectories.
2. Identifies supported audio files: `.flac`, `.mp3`, `.m4a`, and `.opus`.
3. Reads metadata using Mutagen.
4. Extracts embedded front-cover artwork where available.
5. Creates a JSON entry for each successfully read audio file.
6. Generates a list of discovered audio-file directories.

### Metadata collected

| Field | Description |
|---|---|
| `title` | Track title |
| `artist` | Track artist |
| `albumartist` | Album artist |
| `album` | Album name |
| `year` | Release date or year tag |
| `genre` | Genre or comma-separated genres |
| `cover` | Relative web path to the album artwork, or `null` |
| `file` | Relative web path to the audio file |
| `size` | File size in MB |
| `bitrate` | Bitrate in kbps, if available |
| `sample_rate` | Sample rate in kHz, if available |
| `length` | Duration in seconds |
| `file_type` | Audio file extension |

Missing metadata is generally stored as `null` or an empty string, depending on the field.

### Output files

The full scan generates two files inside the music directory:

- **`music.json`** — the complete music library database, containing metadata for all successfully read tracks.
- **`existing_songs_paths.txt`** — a sorted list of the directories containing discovered audio files.

Both files are overwritten during a full scan.

## 2. Incremental Library Update

Add music from one or more specified directories without scanning the entire existing music library.

**Command:**

```bash
python libraryscan.py "C:\Users...\YourLIbraryOfMusic" --update "C:\Music\Artist A\Album 1" "C:\Music\Artist B\Album 2" "C:\Music\Artist C\Album 3" ...
```

Short form:

```bash
python libraryscan.py "C:\Users...\YourLIbraryOfMusic" -u "C:\Music\Artist A\Album 1" "C:\Music\Artist B\Album 2" "C:\Music\Artist C\Album 3" ..."
```

The argument prior to `-u` is always the root music library directory. The paths immediately following `-u` are the folders to import.

### What it does

1. Validates the supplied import directories.
2. Reports invalid directories and skips them.
3. Lists the leaf directories discovered during validation.
4. Requests confirmation before proceeding.
5. Scans supported audio files in the valid directories.
6. Extracts metadata and attempts to extract front-cover artwork.
7. Appends the new track entries to the existing `music.json`.
8. Updates `existing_songs_paths.txt`.

If any supplied directory is invalid, the script asks whether to continue with the valid directories or cancel the update.

**Important:** The update operation appends entries without checking whether those tracks already exist in `music.json`. Importing the same directory twice can therefore create duplicate entries. Use this mode for new, not-yet-imported folders.

## 3. Check Embedded Album Artwork

Use the `--cover` option alongside `--scan` to check whether supported audio files contain embedded artwork.

**Command:**

```bash
python libraryscan.py --scan --cover "C:\Users...\YourLIbraryOfMusic"
```

Short form:

```bash
python libraryscan.py -s -c "C:\Users...\YourLIbraryOfMusic"
```

### What it does

The script recursively examines supported audio files and prints a status for each file:

- `HAS IMAGE` — the file exposes embedded picture data.
- `NO IMAGE` — no picture data was found.
- `ERROR` — an exception occurred while examining the file.

Files without embedded pictures are listed again at the end of the check.

**Note:** This option performs an artwork check, then continues with the full library scan. It is not a standalone artwork-checking mode.

## 4. Command-Line Options

| Option | Description |
|---|---|
| `-h`, `--help` | Display command-line help |
| `-s`, `--scan` | Perform a full library scan |
| `-u`, `--update` | Import one or more directories into the library |
| `-c`, `--cover` | Check embedded artwork before scanning; requires `--scan` |

The script requires exactly one operating mode: `--scan` or `--update`. The root music directory must also be supplied.

To display the available options:

```bash
python libraryscan.py --help
```

## 5. Terminal Output

During a full scan, the terminal displays the file currently being processed:

```text
============================================================
Scanning music library at: "C:\Users...\YourLIbraryOfMusic"
============================================================

Scanning: C:\...\songs\Artist\Album\01 - Track.flac
  ✓ Cover created: Album.jpg

Scanning: C:\...\songs\Artist\Album\02 - Track.flac
  ✓ Cover already exists: Album.jpg

Scanning: C:\...\songs\Artist\Album\03 - Track.mp3
  - No embedded artwork

============================================================
Music library generated successfully!
============================================================
JSON: C:\...\songs\music.json
Existing songs paths .txt file output at: C:\...\songs\existing_songs_paths.txt
Songs found: 3
```

The example above illustrates the output format; actual messages depend on the files encountered.

During an incremental update, the script displays the directories to import, requests confirmation, and finally reports the number of song entries added:

```text
Updating music library at: "C:\Users...\YourLIbraryOfMusic"

Valid directories to add:
  C:\Music\Artist\Album

Continue with the update ? (Invalid directories will be skipped) (y/n): y

Songs added: 12
```

## 6. Error Handling

The script handles several common problems:

- **Root directory not found:** execution terminates with an error.
- **Invalid import directory:** the path is reported and skipped.
- **Unreadable audio file during a full scan:** the error is printed and scanning continues.
- **Missing embedded artwork:** the track is still added to the library.
- **Missing existing `music.json` during an update:** the script starts with an empty library and writes the imported entries.

Some errors in update mode, including certain metadata-reading and artwork-extraction failures, are not caught individually and may terminate the operation.

## 7. Important Usage Considerations

- Always quote Windows paths containing spaces.
- Run a full scan when you need to regenerate the entire library database.
- Use incremental updates to avoid repeatedly processing an established collection.
- Back up `music.json` before importing new music, especially while the update workflow is being developed.
- Avoid importing the same albums more than once.
- Keep the root music folder consistent with the paths expected by the web player.

### Current implementation limitations

The current code has a few behaviors worth knowing before relying on incremental updates:

1. **Duplicate prevention:** the update function does not check existing track paths before appending to `music.json`.
2. **Path-list inconsistency:** a full scan writes album directories to `existing_songs_paths.txt`, while an update adds individual file paths. The update also uses a different set of supported extensions when updating that file.
3. **Artwork paths:** the update function can construct a cover path even when no cover file exists, so the resulting JSON may reference missing artwork.
4. **Update failures:** the update operation does not catch all file-reading or artwork-writing exceptions.

These limitations should be addressed before using incremental imports as a fully reliable library-maintenance workflow.

---

Musibile's library scanner is designed to support large personal music collections by separating initial library generation from incremental imports. A full scan builds the database from the files on disk, while the update mode is intended to add selected folders to an existing library.

Enjoy!
