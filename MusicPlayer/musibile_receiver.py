import sys
import vlc


def format_time(milliseconds):
    if milliseconds < 0:
        return "00:00"

    seconds = milliseconds // 1000
    minutes, seconds = divmod(seconds, 60)

    return f"{minutes:02}:{seconds:02}"


def main():

    if len(sys.argv) < 2:
        print("Usage: python musibile_receiver.py <audio_file>")
        return

    file_path = sys.argv[1]

    # Initialize VLC
    instance = vlc.Instance("--no-video")
    player = instance.media_player_new()

    # Load audio file
    media = instance.media_new(file_path)
    player.set_media(media)

    # Start playback
    player.play()

    print("\nMusibile Receiver started!")
    print(f"Playing: {file_path}")
    print("\nCommands:")
    print("  pause       Pause playback")
    print("  resume      Resume playback")
    print("  stop        Stop playback")
    print("  volume 50   Set volume (0-100)")
    print("  seek 120    Jump to 120 seconds")
    print("  status      Show playback information")
    print("  quit        Exit receiver\n")

    try:
        while True:

            command = input("Musibile > ").strip().split()

            if not command:
                continue

            action = command[0].lower()

            if action == "pause":
                player.set_pause(1)

            elif action == "resume":
                player.set_pause(0)
            elif action == "play":
                if player.get_state() == vlc.State.Paused:
                    player.set_pause(0)
                elif player.get_state() == vlc.State.Stopped:
                    player.play()
                elif player.get_state() == vlc.State.Ended:
                    player.stop()
                    player.play()
            elif action == "stop":
                player.stop()

            elif action == "volume" and len(command) == 2:
                volume = max(0, min(100, int(command[1])))
                player.audio_set_volume(volume)
                print(f"Volume: {volume}%")

            elif action == "seek" and len(command) == 2:
                seconds = max(0, float(command[1]))
                player.set_time(int(seconds * 1000))

            elif action == "status":
                current = player.get_time()
                duration = player.get_length()

                print(f"State: {player.get_state()}")
                print(f"Position: {format_time(current)} / " f"{format_time(duration)}")
                print(f"Volume: {player.audio_get_volume()}%")

            elif action == "quit":
                break

            else:
                print(
                    "Unknown command. Try: pause, resume, stop, volume, seek, status, quit"
                )

    except KeyboardInterrupt:
        print("\nStopping receiver...")

    finally:
        player.stop()
        player.release()
        instance.release()


if __name__ == "__main__":
    main()
