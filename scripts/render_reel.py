# -*- coding: utf-8 -*-
"""Deterministic HTML -> 1080x1920 MP4 Reel renderer (frame capture).

Same architecture as the carousel HTML/Playwright pipeline, extended to
motion: the HTML file owns ALL choreography as a pure function of time
(window.seek(t)), Python steps t frame by frame and screenshots headless
Chromium, ffmpeg assembles H.264 + mixes licensed audio. No CSS
transitions/rAF — every frame is seekable, so renders are reproducible
byte-for-byte at the layout level (Chromium raster differences aside).

HTML contract:
    window.REEL = {duration: <seconds>, fps: 30};
    window.seek(t)  -- lays out the exact visual state at time t.

Audio spec JSON (optional, --audio):
    {"tracks": [{"file": "<repo-relative mp3>", "at": 2.0,
                 "gain_db": -6, "trim": [0, 8.5],
                 "fade_in": 0.3, "fade_out": 1.0}, ...]}
    Mixed with amix normalize=0 + alimiter, cut to video duration.

Usage:
    py -3 scripts/render_reel.py <reel.html> --out <out.mp4> \
        [--audio <spec.json>] [--qa-dir <dir>] [--qa-every 30]

ffmpeg: FFMPEG_BIN env var, else the vendored ffmpeg-static under
income-engine/video_lab (this box has no system ffmpeg).
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FFMPEG = (
    REPO_ROOT.parent
    / "income-engine" / "video_lab" / "samples" / "hyperframes" / ".bin" / "ffmpeg.exe"
)
W, H = 1080, 1920


def ffmpeg_bin() -> str:
    cand = os.environ.get("FFMPEG_BIN") or str(DEFAULT_FFMPEG)
    if not Path(cand).exists():
        raise SystemExit(
            f"FATAL: ffmpeg not found at {cand} — set FFMPEG_BIN to a real binary"
        )
    return cand


def render_frames(html_path: Path, out_silent: Path, qa_dir: Path | None, qa_every: int) -> float:
    """Capture every frame into an H.264 mp4 (no audio). Returns duration (s)."""
    ff = ffmpeg_bin()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(html_path.resolve().as_uri())
        page.wait_for_function("() => window.REEL && typeof window.seek === 'function'")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(400)  # let webfonts settle before frame 0
        meta = page.evaluate("window.REEL")
        duration, fps = float(meta["duration"]), int(meta.get("fps", 30))
        n_frames = round(duration * fps)

        cmd = [
            ff, "-y", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21",
            "-preset", "medium", "-movflags", "+faststart", str(out_silent),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if qa_dir:
            qa_dir.mkdir(parents=True, exist_ok=True)
        try:
            for i in range(n_frames):
                t = i / fps
                page.evaluate(f"window.seek({t})")
                shot = page.screenshot(type="png")
                proc.stdin.write(shot)
                if qa_dir and (i % qa_every == 0 or i == n_frames - 1):
                    (qa_dir / f"f{i:05d}_t{t:06.2f}.png").write_bytes(shot)
                if i % (fps * 5) == 0:
                    print(f"  frame {i}/{n_frames} (t={t:.1f}s)")
            proc.stdin.close()
            rc = proc.wait()
            if rc != 0:
                raise SystemExit(f"FATAL: ffmpeg video assembly exited {rc}")
        finally:
            if proc.poll() is None:
                proc.kill()
            browser.close()
    return duration


def mix_audio(silent: Path, spec_path: Path, duration: float, out_final: Path) -> None:
    ff = ffmpeg_bin()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    tracks = spec["tracks"]
    if not tracks:
        raise SystemExit("FATAL: audio spec has no tracks")
    cmd = [ff, "-y", "-i", str(silent)]
    filters = []
    labels = []
    for idx, tr in enumerate(tracks):
        f = REPO_ROOT / tr["file"]
        if not f.exists():
            raise SystemExit(f"FATAL: audio file missing: {f}")
        cmd += ["-i", str(f)]
        chain = []
        trim = tr.get("trim")
        if trim:
            chain.append(f"atrim=start={trim[0]}:end={trim[1]}")
        chain.append("asetpts=PTS-STARTPTS")
        fade_in = tr.get("fade_in")
        if fade_in:
            chain.append(f"afade=t=in:st=0:d={fade_in}")
        fade_out = tr.get("fade_out")
        if fade_out:
            seg_len = (trim[1] - trim[0]) if trim else None
            if seg_len is None:
                raise SystemExit(
                    f"FATAL: fade_out on track {idx} requires trim so the fade start is known"
                )
            chain.append(f"afade=t=out:st={max(0.0, seg_len - fade_out)}:d={fade_out}")
        gain = tr.get("gain_db", 0)
        chain.append(f"volume={gain}dB")
        delay_ms = int(round(float(tr.get("at", 0)) * 1000))
        chain.append(f"adelay={delay_ms}|{delay_ms}")
        lbl = f"a{idx}"
        filters.append(f"[{idx + 1}:a]{','.join(chain)}[{lbl}]")
        labels.append(f"[{lbl}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:normalize=0:duration=longest,"
        + f"alimiter=limit=0.891,atrim=end={duration},asetpts=PTS-STARTPTS[aout]"
    )
    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        str(out_final),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"FATAL: ffmpeg audio mix failed:\n{res.stderr[-2000:]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--out", required=True)
    ap.add_argument("--audio")
    ap.add_argument("--qa-dir")
    ap.add_argument("--qa-every", type=int, default=30)
    args = ap.parse_args()

    html_path = Path(args.html)
    out_final = Path(args.out)
    out_final.parent.mkdir(parents=True, exist_ok=True)
    silent = out_final.with_suffix(".silent.mp4")

    duration = render_frames(
        html_path, silent, Path(args.qa_dir) if args.qa_dir else None, args.qa_every
    )
    print(f"video assembled: {silent} ({duration}s)")

    if args.audio:
        mix_audio(silent, Path(args.audio), duration, out_final)
        silent.unlink()
        print(f"final with audio: {out_final}")
    else:
        silent.rename(out_final)
        print(f"final (no audio): {out_final}")
    size_mb = out_final.stat().st_size / 1e6
    print(f"size: {size_mb:.1f} MB")
    if size_mb > 90:
        raise SystemExit("FATAL: >90MB — raw.githubusercontent cannot serve this reliably")
    return 0


if __name__ == "__main__":
    sys.exit(main())
