# -*- coding: utf-8 -*-
"""
make_timeline.py —— 按每页口播/配音时长分配画面停留时间，并生成每页一条的精简字幕 srt。

时长规则：
  1) 某页填了 voice_duration（该页单独 TTS 的实测秒数）就直接用，最准；
  2) 否则按 segment 分组，组内按口播稿字数权重（中文 1.0、ASCII 0.55）摊分该段实测时长；
  3) 每页展示时长 = 朗读时长 + gap，避免切镜太急。

字幕规则：每页只放一条“标题式”精简关键字幕，时间落在该页朗读区间内；
不要把整段口播逐句搬上屏，长字幕会挡住卡片正文和人物。

用法：
    python make_timeline.py --config config.json
产出（写在 project_dir）：sub.srt、timeline.json
"""
import argparse, json, io, os


def weight(text, zh=1.0, asc=0.55):
    return sum(zh if ord(c) > 127 else asc for c in text)


def fmt(sec):
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms == 1000:
        s += 1; ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    cfg = json.load(io.open(args.config, encoding="utf-8"))
    root = os.path.abspath(cfg["project_dir"])
    pages = cfg["pages"]
    gap = float(cfg["timeline"]["gap"])
    zh = float(cfg["timeline"]["default_chinese_weight"])
    asc = float(cfg["timeline"]["default_ascii_weight"])

    seg_dur = {s["file"]: float(s.get("duration", 0)) for s in cfg["voice_segments"]}
    # segment 序号 -> 实测时长
    seg_index = {i + 1: float(s.get("duration", 0)) for i, s in enumerate(cfg["voice_segments"])}

    read = [0.0] * len(pages)
    # 先处理直接给定 voice_duration 的页
    for i, p in enumerate(pages):
        if float(p.get("voice_duration", 0)) > 0:
            read[i] = float(p["voice_duration"])

    # 其余页按 segment 分组、字数权重摊分
    groups = {}
    for i, p in enumerate(pages):
        if read[i] > 0:
            continue
        groups.setdefault(p["segment"], []).append(i)
    for seg, idxs in groups.items():
        total_w = sum(weight(pages[i]["voice"], zh, asc) for i in idxs)
        budget = seg_index.get(seg, 0)
        for i in idxs:
            read[i] = budget * weight(pages[i]["voice"], zh, asc) / total_w

    durations = [round(r + gap, 2) for r in read]
    video_dur = round(sum(durations), 2)

    # 精简字幕 srt：每页一条
    srt = []
    acc = 0.0
    for i, p in enumerate(pages):
        s_start = acc + 0.15
        s_end = acc + read[i] - 0.1
        srt.append(f"{i + 1}\n{fmt(s_start)} --> {fmt(s_end)}\n{p['subtitle']}\n")
        acc += durations[i]

    io.open(os.path.join(root, "sub.srt"), "w", encoding="utf-8").write("\n".join(srt))
    timeline = {
        "video_dur": video_dur,
        "read": [round(x, 2) for x in read],
        "durations": durations,
    }
    json.dump(timeline, io.open(os.path.join(root, "timeline.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"video_dur={video_dur}s  页数={len(pages)}", flush=True)
    for i, d in enumerate(durations, 1):
        print(f"  P{i} 朗读{round(read[i-1],2)}s 展示{d}s", flush=True)


if __name__ == "__main__":
    main()
