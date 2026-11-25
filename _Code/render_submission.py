"""Render the caption-free picture and optionally add the original student take."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from imageio_ffmpeg import get_ffmpeg_exe
from render import make_picture

HERE = Path(__file__).resolve().parent
RATE = 48000
BYTES_PER_FRAME = 8


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--voice", type=Path, help="Original student recording, stored locally")
    args = parser.parse_args()
    timeline = json.loads((HERE / "timing.json").read_text())
    ffmpeg = get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as folder:
        temp = Path(folder)
        picture = temp / "picture.mp4" if args.voice else args.output
        make_picture(timeline, temp, picture, ffmpeg, captions=False)
        if not args.voice:
            return

        recording = subprocess.check_output([
            ffmpeg, "-v", "error", "-i", str(args.voice), "-map", "0:a:0",
            "-ar", str(RATE), "-ac", "2", "-c:a", "pcm_f32le", "-f", "f32le", "-",
        ])
        audio = bytearray(round(sum(beat["duration"] for beat in timeline) * RATE) * BYTES_PER_FRAME)
        for edit in json.loads((HERE / "narration_edits.json").read_text()):
            start, end = (round(t * RATE) * BYTES_PER_FRAME for t in edit["source"])
            destination = round(edit["destination"] * RATE) * BYTES_PER_FRAME
            if end > len(recording):
                raise ValueError("The recording is shorter than the saved edit points.")
            audio[destination:destination + end - start] = recording[start:end]
        track = temp / "voice.f32"
        track.write_bytes(audio)
        subprocess.run([
            ffmpeg, "-y", "-v", "error", "-i", str(picture),
            "-f", "f32le", "-ar", str(RATE), "-ac", "2", "-i", str(track),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
            "-b:a", "320k", "-movflags", "+faststart", str(args.output),
        ], check=True)


if __name__ == "__main__":
    main()
