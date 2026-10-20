# -*- coding: utf-8 -*-
"""
build_segments.py —— 把每页截图循环成一段视频，加首尾淡入淡出，再 concat 成无音轨画面。

每页画面：等比缩放后居中 pad 到目标分辨率（不留黑边变形），fps 统一，
开头 0.5s 淡入、结尾 0.5s 淡出，页与页之间柔和过渡，不做花哨转场。

用法：
    python build_segments.py --config config.json
前置：config.pages[].image 就位，make_timeline.py 已生成 timeline.json。
产出（project_dir/segs/）：segN.mp4 与 silent.mp4
"""
import argparse, json, io, os, subprocess


def run(args, cwd, tag):
    r = subprocess.run(args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=cwd)
    if r.returncode != 0:
        raise SystemExit(f"[{tag}] FAIL\n{(r.stdout + r.stderr)[-1200:]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    cfg = json.load(io.open(args.config, encoding="utf-8"))
    root = os.path.abspath(cfg["project_dir"])
    v = cfg["video"]
    W, H, FPS, FADE = v["width"], v["height"], v["fps"], v["fade"]
    pages = cfg["pages"]

    tl = json.load(io.open(os.path.join(root, "timeline.json"), encoding="utf-8"))
    durations = tl["durations"]

    segs_dir = os.path.join(root, "segs")
    os.makedirs(segs_dir, exist_ok=True)

    for i, p in enumerate(pages):
        img = os.path.join(root, p["image"])
        if not os.path.exists(img):
            raise SystemExit(f"缺少页图：{img}")
        dur = durations[i]
        fade_out = round(max(dur - FADE, 0.05), 2)
        segp = os.path.join(segs_dir, f"seg{i + 1}.mp4")
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
              f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS},"
              f"fade=t=in:st=0:d={FADE},fade=t=out:st={fade_out}:d={FADE}")
        run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS),
             "-t", str(dur), "-i", img, "-vf", vf,
             "-c:v", "libx264", "-preset", v["preset"], "-crf", str(v["crf"]),
             "-pix_fmt", "yuv420p", segp], root, f"seg{i+1}")
        print(f"seg{i+1} {dur}s done", flush=True)

    lst = os.path.join(segs_dir, "list.txt")
    io.open(lst, "w", encoding="utf-8").write(
        "".join(f"file 'seg{i+1}.mp4'\n" for i in range(len(pages))))
    silent = os.path.join(segs_dir, "silent.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c", "copy", silent], segs_dir, "concat")
    print(f"silent.mp4 -> {silent}", flush=True)


if __name__ == "__main__":
    main()
