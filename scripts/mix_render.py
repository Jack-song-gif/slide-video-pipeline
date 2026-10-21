# -*- coding: utf-8 -*-
"""
mix_render.py —— 烧录精简字幕、混人人声与压低的 BGM，输出最终成片。

混音：人声 apad 兜底到全长；BGM 循环并压到 bgm_volume（默认 0.12），
只做垫底不盖人声；amix 取最长时长。
字幕：每页一条标题式关键字幕，半透明深色底条（BorderStyle=4），
MarginV 把字幕压在卡片下沿与底部结论条之间的空隙，不遮正文与人物。

用法：
    python mix_render.py --config config.json
前置：build_segments.py 已出 segs/silent.mp4，audio/voice.wav、audio/bgm.wav 就位。
"""
import argparse, json, io, os, subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    cfg = json.load(io.open(args.config, encoding="utf-8"))
    root = os.path.abspath(cfg["project_dir"])
    tl = json.load(io.open(os.path.join(root, "timeline.json"), encoding="utf-8"))
    video_dur = tl["video_dur"]

    sub = cfg["subtitle"]

    # 字幕源优先级：手工定稿的 sub.ass（自带样式，底部居中，已逐页调过 MarginV）优先；
    # 没有 ass 才回退 make_timeline 生成的 sub.srt，并套 force_style。
    # 注意：不要对 ass 再套 force_style，否则会覆盖 ass 里逐页调好的位置/底条。
    ass_path = os.path.join(root, "sub.ass")
    srt_path = os.path.join(root, "sub.srt")
    if os.path.exists(ass_path):
        v_subtitle = "subtitles=sub.ass"
    elif os.path.exists(srt_path):
        style = (
            f"FontName={sub['font']},FontSize={sub['font_size']},"
            "PrimaryColour=&HFFFFFF,OutlineColour=&H00101A26,"
            "BackColour=&H64101A26,BorderStyle=4,Outline=0,Shadow=0,"
            f"MarginV={sub['margin_v']},Alignment={sub['alignment']}"
        )
        v_subtitle = f"subtitles=sub.srt:force_style='{style}'"
    else:
        v_subtitle = None
        raise SystemExit("缺少字幕文件：需要 sub.ass 或 sub.srt")

    silent = os.path.join(root, "segs", "silent.mp4")
    voice = os.path.join(root, cfg["audio"]["voice_wav"])
    bgm = os.path.join(root, cfg["audio"]["bgm_wav"])
    out = os.path.join(root, cfg["output"])
    os.makedirs(os.path.dirname(out), exist_ok=True)

    fc = (
        f"[0:v]{v_subtitle}[v];"
        f"[2:a]volume={cfg['audio']['bgm_volume']},atrim=0:{video_dur}[bg];"
        f"[1:a]apad[vo];"
        f"[vo][bg]amix=inputs=2:duration=longest:dropout_transition=0[a]"
    )
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-i", silent, "-i", voice,
           "-stream_loop", "-1", "-i", bgm,
           "-filter_complex", fc,
           "-map", "[v]", "-map", "[a]", "-t", str(video_dur),
           "-c:v", "libx264", "-preset", cfg["video"]["preset"],
           "-crf", str(cfg["video"]["crf"]),
           "-c:a", "aac", "-b:a", cfg["audio"]["bitrate"], out]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=root)
    if r.returncode != 0:
        raise SystemExit("渲染失败：\n" + r.stderr[-1500:])
    print(f"done -> {out} ({os.path.getsize(out)} bytes, {video_dur}s)", flush=True)


if __name__ == "__main__":
    main()
