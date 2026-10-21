# slide-video-pipeline

把一套分页讲解 PPT 稳定做成 **带口播配音、精简关键字幕、垫底 BGM 的横屏讲解视频**，并配套产出 **横屏 16:9 / 竖屏 9:16 封面**。

面向 AI 工具测评、知识讲解、课程介绍、产品演示这类“翻页 PPT + 旁白解说”的短视频。脚本只做可复用的媒体处理（拼接、计时、淡入淡出、烧字幕、混音、响度核验），内容与审美由创作者决定。

## 链路一览

```
阶段一 PPT 创作/复核 ──► 导出pptx ──► COM矢量渲染1080p整页图
阶段二 分段TTS → 拼接 → 时间线 → 淡入淡出画面 → 烧字幕+混音 → 响度核验（默认1080p）
阶段三 同系列封面锚点换字 → 16:9 横版 + 9:16 竖版
```

详细步骤见 [`references/`](references/)：

- [`references/01-ppt-creation.md`](references/01-ppt-creation.md) —— 分页结构、统一 logo、飞书 Slides 命令模板、改完复核闭环
- [`references/02-voice-tts.md`](references/02-voice-tts.md) —— 分段 TTS、时间线、字幕原则、BGM、成片验收
- [`references/03-cover.md`](references/03-cover.md) —— 横/竖封面版式与锚点换字

## 依赖

- ffmpeg / ffprobe（加入 PATH）
- Python 3.9+（脚本仅用标准库）
- 配音：任意文生语音工具，分段导出 wav
- 可选：飞书 Slides 场景需要 `lark-cli`；Windows 高清页图需要本机 PowerPoint/Office（export_highres_pages.ps1）

## 快速开始

1. 复制配置模板：

```bash
cp config.example.json config.json
```

2. 填写 `config.json`：每页图、所属配音段、口播稿（用于字数权重）、可选单独实测时长、精简字幕；以及各配音段、人声与 BGM 路径。相对路径相对 `project_dir`。

3. 先把导出的 pptx 渲染成高清整页图（Windows，PowerPoint COM），并把每页图路径填进 config：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/export_highres_pages.ps1 `
  -Pptx "./out/deck.pptx" -OutDir "./highres" -Width 1920 -Height 1080
```

4. 按顺序执行：

```bash
python scripts/concat_voice.py    --config config.json   # 分段TTS拼接，回读每段时长
python scripts/make_timeline.py   --config config.json   # 分配页时长，生成 sub.srt / timeline.json
python scripts/build_segments.py  --config config.json   # 高清页图→带淡入淡出的画面并 concat
python scripts/mix_render.py      --config config.json   # 烧字幕 + 人声/BGM 混音出成片
python scripts/check_volume.py    --config config.json   # volumedetect 响度核验
```

## 脚本说明

| 脚本 | 职责 |
|---|---|
| `concat_voice.py` | 分段 TTS wav 按序 concat 成 voice.wav，ffprobe 回读每段时长并写回 config |
| `make_timeline.py` | 优先用每页单独实测时长，否则按 segment 内字数权重摊分；生成 `sub.srt`（每页一条关键字幕）与 `timeline.json` |
| `build_segments.py` | 高清页图 loop 成段，等比缩放居中 pad 到 config 分辨率（默认1920×1080），首尾淡入淡出，concat 成无音轨 silent.mp4 |
| `mix_render.py` | 烧录关键字幕（优先手写 sub.ass，回退 sub.srt+force_style），人声 apad 兜底，BGM 循环压到 0.12，amix 出成片 |
| `check_volume.py` | 打印 mean / max volume，核验不爆音、人声不被压 |
| `export_highres_pages.ps1` | Windows：PowerPoint COM 把导出的 pptx 矢量渲染成 1920×1080 整页 PNG（自动处理中文/空格路径），作为视频高清画面源 |

## 关键纪律

- **默认输出 1920×1080 高清**（crf16/preset slow），不要回退 720p；视频画面用 pptx 矢量渲染的高清整页图，不要把 960×540 在线截图放大当画面。
- 长口播必须**分段 TTS**（每段 ≤90s），单条整稿会被语音上限截断。
- 每页只放**一条标题式精简字幕**，不做逐句长字幕，字幕不遮正文与人物；定稿字幕优先手写 sub.ass。
- BGM 只垫底（默认 0.12），人声为主；全片配音音色统一。
- 封面保持同一角色形象，横竖版分别锁定比例，不拉伸。

## 目录

```
slide-video-pipeline/
├── SKILL.md
├── README.md
├── config.example.json
├── scripts/
├── references/
└── assets/        # 账号 logo、形象底稿等品牌素材（自行放入，不随仓库分发）
```
