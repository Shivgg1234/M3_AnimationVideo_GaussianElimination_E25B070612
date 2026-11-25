"""Build the guide MP4, silent picture master and a timing manifest."""

import argparse
from io import BytesIO
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import wave

from imageio_ffmpeg import get_ffmpeg_exe
from piper import PiperVoice, SynthesisConfig

from project import BEATS
from visuals import X_STEPS, Y_STEPS, frame

FPS = 24
RATE = 22050
VOICE_DELAY = 0.5
BREAK = 0.19
VOICE_CONFIG = SynthesisConfig(length_scale=1.035, volume=0.83)
ANIMATIONS = {
    "cover": [(1,4.2)], "hook": [(0,1.6)], "system": [(0,1.6)],
    "augment": [(1.3,3.45)], "rules": [(0,1.1),(2.5,3.6),(5,6.1)],
    "lines": [(0.7,2.45),(4.65,6.75),(8.1,8.2)],
    "rotate": [(5.45,12.25)], "reverse": [(8.15,13.25)], "swap": [(7.15,10.65)],
    "eliminate_x": [(2.55,4.05), *((s,s+0.72) for s in X_STEPS)],
    "predict": [(9.4,14)], "eliminate_y": [(s,s+0.72) for s in Y_STEPS],
    "echelon": [(0.5,3.05)],
    "solve_z": [(s,s+0.65) for s in (0.22,4.6,7.15)],
    "solve_y": [(s,s+0.65) for s in (0.22,4.6,7.15,9.8)]+[(3.08,4.57)],
    "solve_x": [(s,s+0.65) for s in (0.22,4.6,7.15,9.8)]+[(3.08,4.57)],
    "verify": [(s,s+0.83) for s in (3.2,6.2,9.2)],
    "planes": [(0.32,16.55)], "slice": [(7.95,11.05)],
    "recap": [(0.23,1.23),(2.73,3.73),(5.23,6.23)],
}
FULL_RATE = {"rotate", "reverse", "swap", "planes", "predict"}

def silence(duration):
    return bytes(2*round(duration*RATE))

def make_voice(model, path):
    voice = PiperVoice.load(model)
    if voice.config.sample_rate != RATE:
        raise ValueError(f"This voice model must have a {RATE} Hz sample rate.")
    timeline = []
    position = 0
    with wave.open(str(path), "wb") as track:
        track.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        for key, chapter, minimum, heading, narration in BEATS:
            clips = []
            cues = []
            cursor = VOICE_DELAY
            for sentence in re.split(r"(?<=[.!?])\s+", narration):
                buffer = BytesIO()
                names = {"x": "ex", "y": "why", "z": "zee"}
                spoken = re.sub(r"\b[xyz]\b", lambda match: names[match.group()], sentence)
                with wave.open(buffer, "wb") as clip:
                    voice.synthesize_wav(spoken, clip, syn_config=VOICE_CONFIG)
                buffer.seek(0)
                with wave.open(buffer, "rb") as clip:
                    duration = clip.getnframes()/RATE
                    if duration < 0.25:
                        raise ValueError(f"Missing narration in {key}.")
                    clips.append(clip.readframes(clip.getnframes()))
                cues.append((cursor, cursor+duration+0.09, sentence))
                cursor += duration+BREAK
            duration = math.ceil(max(minimum, cursor+0.9)*FPS)/FPS
            track.writeframes(silence(VOICE_DELAY))
            for clip in clips:
                track.writeframes(clip)
                track.writeframes(silence(BREAK))
            track.writeframes(silence(duration-cursor))
            timeline.append(dict(key=key, chapter=chapter, heading=heading, narration=narration,
                                 start=position, duration=duration, cues=cues))
            position += duration
            print(f"Narration {key:13} {cursor:5.2f} s audio, {duration:5.2f} s scene", flush=True)
    return timeline

def visual_ticks(beat):
    length = round(beat["duration"]*FPS)
    ticks = set(range(0,length,FPS*2)) | {0,length}
    for start, stop in ANIMATIONS.get(beat["key"], []):
        ticks.update(range(round(start*FPS),min(length,round(stop*FPS)),1 if beat["key"] in FULL_RATE else 2))
        ticks.add(min(length,round(stop*FPS)))
    for start, stop, _ in beat["cues"]:
        ticks.update((round(start*FPS), min(length,round(stop*FPS))))
    return sorted(ticks)

def make_picture(timeline, temp, dest, ffmpeg, captions=True):
    total = sum(beat["duration"] for beat in timeline)
    frames = temp/"frames"
    frames.mkdir()
    concat = temp/"frames.ffconcat"
    index = 0
    with concat.open("w") as sequence:
        sequence.write("ffconcat version 1.0\n")
        for beat in timeline:
            ticks = visual_ticks(beat)
            for left, right in zip(ticks,ticks[1:]):
                t = left/FPS
                caption = next((capt for a,b,capt in beat["cues"] if round(a*FPS)<=left<round(b*FPS)), "")
                if not captions:
                    caption = ""
                filename = f"frames/{index:05d}.jpg"
                image = frame(beat["key"], beat["chapter"], beat["heading"], t, caption,
                              beat["start"]+t, total)
                image.save(temp/filename, quality=96, subsampling=0)
                sequence.write(f"file {filename}\noption framerate {FPS}\nduration {(right-left)/FPS:.9f}\n")
                index += 1
            print(f"Animated {beat['key']}", flush=True)
        sequence.write(f"file frames/{index-1:05d}.jpg\noption framerate {FPS}\n")
    subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "warning", "-nostats",
                    "-f", "concat", "-safe", "0", "-i", str(concat), "-t", f"{total:.6f}",
                    "-vf", f"fps={FPS},scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-movflags", "+faststart", str(dest)], check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True, help="Path to the Piper Lessac medium ONNX model")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timing-dir", type=Path, help="Save the timing manifest in this directory")
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=True)
    if options.timing_dir:
        options.timing_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = get_ffmpeg_exe()
    with tempfile.TemporaryDirectory(prefix="gaussian-render-") as directory:
        temp = Path(directory)
        voice_path = temp/"narration.wav"
        timeline = make_voice(options.model, voice_path)
        if options.timing_dir:
            (options.timing_dir/"timing.json").write_text(json.dumps(timeline, indent=2, ensure_ascii=False))
        silent = options.output/"Gaussian_Elimination_V2_Voiceover_Ready.mp4"
        make_picture(timeline, temp, silent, ffmpeg)
        subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "warning", "-nostats",
                        "-i", str(silent), "-i", str(voice_path), "-c:v", "copy",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", "48000",
                        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
                        str(options.output/"Gaussian_Elimination_V2_Video.mp4")], check=True)

if __name__ == "__main__":
    main()
