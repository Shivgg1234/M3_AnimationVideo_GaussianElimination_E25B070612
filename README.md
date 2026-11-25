# Gaussian elimination

M3 Linear Algebra and Calculus animation by Tanishq Gupta, E25B070612, Batch Neumann.

- `_Video.mp4` is the final six-minute 1080p animation with student narration.
- `_Code/` contains the editable animation, scene timings, and narration sync points.
- `Storyboard.pdf` outlines all six scenes.
- `Voiceover_Script.pdf` contains the timed recording script.

## Rebuild

Use Python 3.10 or newer. The renderer uses system Arial, Georgia, and Menlo on macOS, with DejaVu fallbacks.

```sh
python3 -m pip install -r _Code/requirements.txt
python3 _Code/render_submission.py --output picture.mp4
```

To include the student narration, add `--voice /path/to/original-recording.m4a` to the render command. The original recording is kept separately. The published MP4 already includes the synchronized track.

## Credits

The student recorded the final narration. OpenAI Codex assisted with scripting, original visuals, animation code, and narration synchronization. Piper / Lessac was used in the rehearsal guide. No background music was used.

Reference: [OpenStax, Algebra and Trigonometry 2e, §11.6](https://openstax.org/books/algebra-and-trigonometry-2e/pages/11-6-solving-systems-with-gaussian-elimination).
