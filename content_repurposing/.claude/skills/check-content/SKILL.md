---
name: check-content
description: Check what content has been generated — lists scripts, audio, and subtitle files in the generated_content folder
---

List and summarize the generated content in this pipeline project.

Run these commands and report back clearly:

Files in generated_content/scripts/: !`ls generated_content/scripts/ 2>/dev/null || echo "(empty)"`
Files in generated_content/audio/: !`ls generated_content/audio/ 2>/dev/null || echo "(empty)"`
Files in generated_content/subtitles/: !`ls generated_content/subtitles/ 2>/dev/null || echo "(empty)"`

For each folder, show:
- How many files are in it
- The file names (without full paths)
- If a folder is empty, say so clearly

Keep it short and clean. If $ARGUMENTS is provided, filter results to only show files matching that keyword.
