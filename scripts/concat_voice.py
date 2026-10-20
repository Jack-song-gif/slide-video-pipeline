# -*- coding: utf-8 -*-
"""
concat_voice.py —— 把分段 TTS 配音按顺序拼接为一条完整人声。

为什么分段：文生语音单条通常有上限（如约 120s），长口播必须分段生成，
再在本地用 ffmpeg concat 拼成完整 voice.wav，并回读每段实际时长供时间线分配。

用法：
    python concat_voice.py --config config.json
前置：config.voice_segments 已按顺序列出每段 wav（相对 project_dir）。
"""
import argparse, json, os, subprocess, io


def probe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "json", path],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    data = json.loads(r.stdout)
    return round(float(data["format"]["duration"]), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    cfg = json.load(io.open(args.config, encoding="utf-8"))
    root = os.path.abspath(cfg["project_dir"])
    segs = cfg["voice_segments"]
    if not segs:
        raise SystemExit("voice_segments 为空，无需拼接")

    audio_dir = os.path.join(root, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    lst = os.path.join(audio_dir, "voice_concat_list.txt")

    resolved = []
    for s in segs:
        p = os.path.join(root, s["file"])
        if not os.path.exists(p):
            raise SystemExit(f"缺少配音段：{p}")
        d = probe_duration(p)
        s["duration"] = d
        resolved.append(p)
        print(f"[seg] {os.path.basename(p)}  dur={d}s", flush=True)

    # concat 列表用相对 audio_dir 的文件名，保证 -c copy 可定位
    with io.open(lst, "w", encoding="utf-8") as f:
        for p in resolved:
            f.write(f"file '{os.path.basename(p)}'\n")

    voice_wav = os.path.join(root, cfg["audio"]["voice_wav"])
    os.makedirs(os.path.dirname(voice_wav), exist_ok=True)
    r = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c", "copy", voice_wav],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=audio_dir)
    if r.returncode != 0:
        raise SystemExit("拼接失败：\n" + r.stderr[-800:])

    total = probe_duration(voice_wav)
    cfg["voice_total"] = total
    io.open(args.config, "w", encoding="utf-8").write(
        json.dumps(cfg, ensure_ascii=False, indent=2))
    print(f"voice.wav 总时长={total}s -> {voice_wav}", flush=True)


if __name__ == "__main__":
    main()
