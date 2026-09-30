import os
import mutagen

music_folder = r"G:\Music"
no_picture_file = []

for root, dirs, files in os.walk(music_folder):

    for file in files:

        if not file.lower().endswith(".flac"):
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
print("\n\nFiles without embedded images:")
for file in no_picture_file:
    print(file)
