# Lecture decks

One folder per subject that uses lecture slides:

```text
data/lecturedecks/CSC662/   decks for CSC662, when stored locally
data/lecturedecks/CSC580/   create when that subject is implemented
```

The loader prefers `data/lecturedecks/<SUBJECT>/` when it contains `.pptx`
files. If the folder is empty, CSC662 falls back to `CSC662_DECKS_DIR`
(default `~/Desktop/CSC662`). Set `<SUBJECT>_DECKS_DIR` to override either.

Decks are read-only. They are intentionally not copied into the repository by
default because they are large course material.
