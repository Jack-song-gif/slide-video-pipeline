# -*- coding: utf-8 -*-
"""
check_volume.py —— 用 ffmpeg volumedetect 检查成片整体响度。

验收参考：mean_volume 通常在 -30 ~ -20 dB，max_volume 不宜高于 -3 dB（避免爆音）；
若 max_volume 过高则在混音前对人声单独限幅，而不是继续压低 BGM。

用法：
    python check_volume.py --config config.json
    python check_volume.py --file path/to/video.mp4
"""
import argparse, json, io, os, subprocess


def detect(path):
    r = subprocess.run(["ffmpeg", "-i", path, "-af", "volumedetect",
                        "-f", "null", "-"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    for line in r.stderr.splitlines():
        if "mean_volume" in line or "max_volume" in line:
            print(line.strip(), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--file")
    args = ap.parse_args()
    if args.file:
        detect(args.file); return
    cfg = json.load(io.open(args.config, encoding="utf-8"))
    root = os.path.abspath(cfg["project_dir"])
    detect(os.path.join(root, cfg["output"]))


if __name__ == "__main__":
    main()
