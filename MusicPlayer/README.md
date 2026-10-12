Musibile 🎵

A self-hosted personal music library and web-based music player built for high-quality local music streaming.

Musibile is a personal music server project designed to make a large local music collection accessible through a custom web interface. It combines a lightweight web-based music player with Python-powered library management, allowing you to organize, browse, search, and play your music directly from your own computer.

Built with a focus on simplicity, customization, and self-hosting, Musibile is designed to handle a large music collection without relying on third-party streaming platforms or cloud music services.

✨ Features

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

🛠️ Technologies

HTML, CSS, and JavaScript — Frontend interface and playback logic.

Python — Music metadata scanning, artwork extraction, and album importing.

Mutagen — Reading audio metadata and embedded artwork.

JSON — Storing and exchanging music library metadata.

HTTP server — Hosting the web interface and music files.

Tailscale — Optional private-network connectivity for accessing the server remotely.

📚 Library Management

Musibile includes Python scripts for scanning music directories and extracting metadata from supported audio files. The scanner collects information such as track titles, artists, albums, genres, and release years, while also extracting embedded front-cover artwork where available.

An incremental album-import workflow is intended to make library maintenance more efficient: instead of processing the entire collection every time, you can specify the album directories you want to add.

This approach is particularly useful for large libraries containing thousands of tracks.

🌐 Self-Hosting

The project is designed to run on your own computer, which acts as the music server. Other devices can access the web player through a browser over the same local network.

With an appropriately configured private network, such as Tailscale, the player can also be accessed remotely without making the music server publicly accessible to the entire internet.

📱 Responsive Interface

The player is designed for desktop and mobile use, with a compact layout, album artwork animations, touch-based track navigation, and familiar playback controls.

🎯 Project Goals

Build a personal alternative to cloud-based music streaming.

Keep control of the music library and its storage.

Make large local music collections easier to browse and maintain.

Learn and apply Python, JavaScript, HTML, and CSS through a practical project.

Explore self-hosting, networking, metadata processing, and media delivery.

🚧 Project Status

Musibile is an ongoing personal project. Features, performance, and library-management workflows are being refined as the project develops.

🔒 Privacy and Ownership

Your music library remains on your own hardware. The project is intended for personal use, giving you control over your files, library organization, and access to your music.

Built as a personal project to combine music, programming, and self-hosted infrastructure.