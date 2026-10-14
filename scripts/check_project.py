#!/usr/bin/env python3
"""Check a hand-drawn MV manifest and its assets; does not judge visual quality."""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class Check:
    def __init__(self, manifest, root):
        self.m = manifest
        self.root = root
        self.errors = []
        self.warnings = []
        self.slots = []
        self.assets = []
        self.stats = {}

    def error(self, message):
        self.errors.append(message)

    def warn(self, message):
        self.warnings.append(message)

    def path(self, value):
        return (self.root / value).resolve()

    def plan(self):
        m = self.m
        if not isinstance(m, dict):
            self.error("Manifest must be an object")
            return
        if m.get("version") != 1:
            self.error("Manifest version must be 1")
        for field in ("duration", "fps"):
            if not number(m.get(field)) or m[field] <= 0:
                self.error(f"{field} must be a positive finite number")
        for field in ("width", "height"):
            if type(m.get(field)) is not int or m[field] <= 0 or m[field] % 2:
                self.error(f"{field} must be a positive even integer for this MP4 workflow")
        if type(m.get("audio_required", True)) is not bool:
            self.error("audio_required must be boolean")
        r = m.get("requirements", {})
        if not isinstance(r, dict):
            self.error("requirements must be an object")
            return
        minimum = r.get("min_character_keyframes", 2)
        if type(minimum) is not int or minimum < 1:
            self.error("min_character_keyframes must be a positive integer")
            minimum = 2
        for field in ("all_shots_need_character", "unique_assets", "requires_alpha"):
            if field in r and type(r[field]) is not bool:
                self.error(f"requirements.{field} must be boolean")
        shots = m.get("shots")
        if not isinstance(shots, list) or not shots:
            self.error("shots must be a nonempty list")
            return
        last_end, shot_ids, paths = 0, set(), {}
        for index, shot in enumerate(shots):
            label = f"shot[{index}]"
            if not isinstance(shot, dict):
                self.error(f"{label}: must be an object")
                continue
            sid = shot.get("id")
            if not nonempty(sid) or sid in shot_ids:
                self.error(f"{label}: id must be a unique nonempty string")
            else:
                shot_ids.add(sid)
                label = f"shot {sid}"
            start, end = shot.get("start"), shot.get("end")
            if not number(start) or not number(end) or start < 0 or end <= start:
                self.error(f"{label}: invalid time range")
            else:
                if abs(start - last_end) > 0.001:
                    self.error(f"{label}: gap/overlap; start {start}, previous end {last_end}")
                last_end = end
            character = shot.get("character")
            if type(character) is not bool:
                self.error(f"{label}: character must be boolean")
            if r.get("all_shots_need_character", False) and character is not True:
                self.error(f"{label}: all shots require character artwork")
            for field in ("action", "framing"):
                if not nonempty(shot.get(field)):
                    self.error(f"{label}: missing {field}")
            frames = shot.get("keyframes", [])
            if not isinstance(frames, list):
                self.error(f"{label}: keyframes must be a list")
                continue
            if character and len(frames) < minimum:
                self.error(f"{label}: needs {minimum} character keyframes; has {len(frames)}")
            frame_ids = set()
            for key in frames:
                if not isinstance(key, dict):
                    self.error(f"{label}: keyframe must be an object")
                    continue
                kid = key.get("id")
                if not nonempty(kid) or kid in frame_ids:
                    self.error(f"{label}: keyframe id must be a unique nonempty string")
                else:
                    frame_ids.add(kid)
                tag = f"{label}/{kid}"
                if not nonempty(key.get("pose")):
                    self.error(f"{tag}: missing pose description")
                if "allow_edge_crop" in key and type(key["allow_edge_crop"]) is not bool:
                    self.error(f"{tag}: allow_edge_crop must be boolean")
                if not nonempty(key.get("file")):
                    self.error(f"{tag}: missing asset path")
                    continue
                path = self.path(key["file"])
                if r.get("unique_assets", True) and path in paths:
                    self.error(f"{tag}: repeats asset path used by {paths[path]}")
                paths[path] = tag
                self.slots.append((tag, key, path, sid))
        if number(m.get("duration")) and abs(last_end - m["duration"]) > 0.001:
            self.error(f"Timeline ends at {last_end}; target duration is {m['duration']}")
        self.stats.update(shots=len(shots), planned_keyframes=len(self.slots),
                          unique_planned_paths=len(paths))

    def images(self):
        from PIL import Image
        hashes, sizes = {}, {}
        r = self.m.get("requirements", {})
        for tag, key, path, sid in self.slots:
            try:
                with Image.open(path) as source:
                    im = source.convert("RGBA")
            except (OSError, ValueError) as exc:
                self.error(f"{tag}: cannot read {key['file']}: {exc}")
                continue
            alpha = im.getchannel("A")
            low, high = alpha.getextrema()
            bounds = alpha.getbbox()
            if high == 0:
                self.error(f"{tag}: asset is fully transparent")
            if r.get("requires_alpha", True) and low != 0:
                self.error(f"{tag}: no fully transparent pixels; check real alpha background")
            # Premultiplication ignores invisible RGB values in alpha=0 pixels.
            digest = hashlib.sha256(str(im.size).encode() + im.convert("RGBa").tobytes()).hexdigest()
            if r.get("unique_assets", True) and digest in hashes:
                self.error(f"{tag}: duplicate decoded image of {hashes[digest]}")
            hashes[digest] = tag
            if sid in sizes and sizes[sid] != im.size:
                self.error(f"{tag}: paired canvas size differs: {im.size} vs {sizes[sid]}")
            sizes[sid] = im.size
            if bounds:
                margin = min(bounds[0], bounds[1], im.width - bounds[2], im.height - bounds[3])
                if margin < 2 and not key.get("allow_edge_crop", False):
                    self.warn(f"{tag}: silhouette touches/approaches canvas edge; inspect cropping")
            self.assets.append({"slot": tag, "file": key["file"], "size": list(im.size),
                                "alpha_range": [low, high], "bounds": bounds, "pixel_sha256": digest})
        self.stats.update(readable_assets=len(self.assets), unique_decoded_images=len(hashes))
        self.warn("Pixel hashes do not detect mirrored/recolored poses or judge anatomy; visually inspect every pair")

    def usage(self, path):
        usage = read_json(path)
        if not isinstance(usage, dict) or not isinstance(usage.get("used_keyframes"), list):
            self.error("Usage must contain used_keyframes: list of manifest-relative asset paths")
            return
        listed = usage["used_keyframes"]
        if not all(nonempty(item) for item in listed):
            self.error("Every used_keyframes entry must be a nonempty asset path")
            return
        used = {self.path(item) for item in listed}
        expected = {slot[2] for slot in self.slots}
        for missing in sorted(expected - used):
            self.error(f"Planned asset absent from render usage: {missing}")
        counts = usage.get("shown_frames")
        if counts is not None:
            if not isinstance(counts, dict) or not all(nonempty(k) for k in counts):
                self.error("shown_frames must map asset paths to positive integer frame counts")
            else:
                normalized = {self.path(k): v for k, v in counts.items()}
                for asset in expected:
                    count = normalized.get(asset, 0)
                    if type(count) is not int or count <= 0:
                        self.error(f"No positive shown_frames count for {asset}")
        self.stats["planned_assets_recorded_in_usage"] = len(expected & used)
        self.warn("Usage logs prove reported drawing only; inspect the movie for occlusion and readable pose changes")

    def video(self, path, decode):
        if not shutil.which("ffprobe"):
            self.error("ffprobe not found")
            return
        result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                                 "-of", "json", str(path.resolve())], capture_output=True, text=True)
        if result.returncode:
            self.error("ffprobe failed: " + result.stderr[-1500:])
            return
        probe = json.loads(result.stdout)
        streams = probe.get("streams", [])
        videos = [s for s in streams if s.get("codec_type") == "video"]
        audios = [s for s in streams if s.get("codec_type") == "audio"]
        if not videos:
            self.error("No video stream")
            return
        stream = videos[0]
        self.stats["video"] = {k: stream.get(k) for k in
                               ("width", "height", "avg_frame_rate", "nb_frames", "codec_name", "duration")}
        self.stats["video"]["audio_streams"] = len(audios)
        for field in ("width", "height"):
            if stream.get(field) != self.m[field]:
                self.error(f"Video {field} is {stream.get(field)}, expected {self.m[field]}")
        try:
            actual_fps = float(Fraction(stream["avg_frame_rate"]))
            if abs(actual_fps - self.m["fps"]) > 0.01:
                self.error(f"Video fps is {actual_fps}, expected {self.m['fps']}")
        except (KeyError, ValueError, ZeroDivisionError):
            self.error("Cannot determine video frame rate")
        raw_duration = stream.get("duration", probe.get("format", {}).get("duration"))
        try:
            duration = float(raw_duration)
            if not math.isfinite(duration) or abs(duration - self.m["duration"]) > 1 / self.m["fps"] + 0.005:
                self.error(f"Video duration is {duration}, expected {self.m['duration']}")
        except (TypeError, ValueError):
            self.error("Cannot determine video duration")
        frames = stream.get("nb_frames", "")
        expected_frames = round(self.m["duration"] * self.m["fps"])
        if str(frames).isdigit():
            if abs(int(frames) - expected_frames) > 1:
                self.error(f"Video has {frames} frames; expected about {expected_frames}")
        else:
            self.warn("Container does not expose nb_frames; frame count was not verified")
        if self.m.get("audio_required", True) and not audios:
            self.error("Required audio stream is missing")
        if decode:
            if not shutil.which("ffmpeg"):
                self.error("ffmpeg not found; cannot decode")
            else:
                result = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path.resolve()),
                                         "-map", "0:v:0", "-map", "0:a?", "-f", "null", "-"],
                                        capture_output=True, text=True)
                self.stats["decode_passed"] = result.returncode == 0 and not result.stderr.strip()
                if not self.stats["decode_passed"]:
                    self.error("Full decode failed: " + result.stderr[-1500:])

    def contact_sheet(self, output):
        from PIL import Image, ImageDraw
        if not self.assets:
            self.error("Cannot create contact sheet: no readable assets")
            return
        cols, tw, th = 4, 240, 290
        rows = math.ceil(len(self.assets) / cols)
        sheet = Image.new("RGB", (cols * tw, rows * th), (236, 229, 220))
        draw = ImageDraw.Draw(sheet)
        for i, asset in enumerate(self.assets):
            with Image.open(self.path(asset["file"])) as source:
                im = source.convert("RGBA")
            im.thumbnail((tw - 16, th - 40))
            x, y = (i % cols) * tw, (i // cols) * th
            sheet.paste(im, (x + (tw - im.width) // 2, y + 24), im)
            draw.text((x + 8, y + 5), f"{i + 1:02d}: {asset['slot']}", fill=(40, 35, 30))
        output.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output)
        self.stats["contact_sheet"] = str(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--video", type=Path)
    parser.add_argument("--usage", type=Path)
    parser.add_argument("--decode", action="store_true")
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.plan_only and (args.video or args.usage or args.decode or args.contact_sheet):
        parser.error("--plan-only cannot be combined with asset/video/usage checks")
    if args.decode and not args.video:
        parser.error("--decode requires --video")
    check = Check({}, args.manifest.resolve().parent)
    try:
        check.m = read_json(args.manifest)
        check.plan()
        if not check.errors and not args.plan_only:
            check.images()
            if args.usage:
                check.usage(args.usage)
            if args.video:
                check.video(args.video, args.decode)
            if args.contact_sheet:
                check.contact_sheet(args.contact_sheet)
    except (OSError, ValueError, ImportError) as exc:
        check.error(f"Check could not complete: {exc}")
    report = {"passed": not check.errors, "mode": "plan" if args.plan_only else "assets",
              "summary": check.stats, "errors": check.errors, "warnings": check.warnings,
              "assets": check.assets,
              "limits": "No automated check of pose semantics, anatomy, visual visibility, rhythm, or audio sync"}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
