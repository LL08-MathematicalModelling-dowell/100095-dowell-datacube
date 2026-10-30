# Playground demo media

Files in this folder are **uploaded into GridFS** when a new playground session
starts (`seed_playground_sample_files_sync`).

Expected names (preferred):

- `beautiful-fall-nature-scenery-free-image.jpeg`
- `file_test_demo.mp4`

If those are missing, any `.jpg` / `.jpeg` / `.png` / `.webp` / `.gif` / `.mp4` /
`.webm` / `.pdf` in this directory is used instead.

Keep samples small — they are copied into Mongo for every new playground user.
