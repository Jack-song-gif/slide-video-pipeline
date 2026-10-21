---
name: slide-video-pipeline
description: 把一份讲解类 PPT（飞书 Slides / 图片页）做成带口播配音、精简关键字幕、压低 BGM 的横屏讲解视频，并配套产出横屏 16:9 与竖屏 9:16 封面。适用于 AI 工具测评、知识讲解、课程介绍、产品演示等“翻页 PPT + 旁白解说”类短视频。覆盖 PPT 创作与复核、分段 TTS 拼接、按页时长分配、页间淡入淡出、字幕烧录、人声/BGM 混音、响度核验与双比例封面。当用户要求“把 PPT 做成讲解视频/口播视频”“给 PPT 配旁白并合成视频”“做视频横版竖版封面”时使用。
---

# Slide → Video Pipeline（PPT 讲解视频 + 封面工作流）

把一套分页讲解 PPT，稳定产出成一条带旁白、关键字幕、垫底 BGM 的横屏讲解视频，并配横/竖两张封面。整条链路经过真实项目验证，脚本只做可复用的媒体处理，内容创作与审美判断由执行者完成。

## 前置依赖

- `ffmpeg` / `ffprobe`（画面分段、concat、字幕烧录、混音、响度检测）
- `python` 3.9+（标准库即可，脚本无第三方依赖）
- 配音：可用任意文生语音工具分段生成 wav；PPT 阶段若用飞书 Slides，需要 `lark-cli`
- **Windows 高清页图（推荐）**：本机安装 PowerPoint/Office，用 `scripts/export_highres_pages.ps1`（COM）把导出的 pptx 矢量渲染成 1920×1080 整页图；没有 PowerPoint 时才退而用在线截图，但必须知道其只有 960×540、放大发糊。

## 输出规格（默认高清）

- 成片默认 **1920×1080 / 30fps / crf16 / preset slow**，不要为省体积回到 720p。
- 视频画面源必须是**高清整页图**（1920×1080）：飞书 `+screenshot` 固定只有 960×540，仅用于服务端复核，不能直接当视频画面放大使用。

## 目录结构

```
slide-video-pipeline/
├── SKILL.md                  # 本入口
├── README.md                 # 项目说明与快速开始
├── config.example.json       # 配置模板，复制为 config.json 使用
├── scripts/
│   ├── concat_voice.py       # 分段 TTS 拼接成 voice.wav 并回读时长
│   ├── make_timeline.py     # 按页时长分配 + 生成 sub.srt / timeline.json
│   ├── build_segments.py     # 页图→带淡入淡出的视频段并 concat
│   ├── mix_render.py        # 烧字幕（优先 sub.ass）+ 人声/BGM 混音出成片
│   ├── check_volume.py      # volumedetect 响度核验
│   └── export_highres_pages.ps1  # Windows：PowerPoint COM 把 pptx 矢量渲染成1080p整页图
├── references/
│   ├── 01-ppt-creation.md   # 阶段一：飞书 Slides 创作、加 logo、复核、导出
│   ├── 02-voice-tts.md      # 阶段二：分段 TTS、时间线、字幕、BGM、验收
│   └── 03-cover.md          # 阶段三：横/竖封面版式与锚点换字
└── assets/                  # 账号 logo、形象底稿等品牌素材（按需放入）
```

## 执行流程

### 阶段一 · PPT 创作与复核
读 `references/01-ppt-creation.md`。组织 7–9 页分页结构，每页右上角统一 logo，关键事实/链接做成卡片条；改完必须 `xml-get` 复核 0 error 0 warning、逐页 `+screenshot` 肉眼检查、导出 pptx。

> **在线截图（+screenshot，960×540）只用于服务端复核，不是视频画面源。** 视频画面用导出的 pptx 经 `scripts/export_highres_pages.ps1` 矢量渲染成 1920×1080 整页图（见下），再填进 `config.json` 的 `pages[].image`。

```powershell
# Windows：把导出的 pptx 渲染成高清整页图（脚本自动处理中文/空格路径）
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/export_highres_pages.ps1 `
  -Pptx "./out/deck.pptx" -OutDir "./highres" -Width 1920 -Height 1080
```

### 阶段二 · 配音与成片
读 `references/02-voice-tts.md`。关键纪律：

1. **长口播必须分段 TTS**（每段 ≤90s），单条整稿会被 120s 上限截断；用 `concat_voice.py` 拼接。
2. 每页只放**一条标题式精简关键字幕**，不做逐句长字幕，字幕压在画面空隙、不遮正文与人物。定稿字幕优先用手写 `sub.ass`（底部居中、逐页调过 MarginV），`mix_render.py` 检测到 ass 会直接采用其样式，不再套 force_style。
3. BGM 压到 0.12 垫底，人声为主。
4. 画面默认 1080p：`pages[].image` 必须指向高清整页图，`build_segments.py` 按 config 的 1920×1080 pad/淡入淡出。

按顺序执行：

```bash
python scripts/concat_voice.py    --config config.json
python scripts/make_timeline.py    --config config.json
python scripts/build_segments.py   --config config.json
python scripts/mix_render.py      --config config.json
python scripts/check_volume.py    --config config.json
```

可选 1.2x 保调加速版：画面 `setpts=PTS/1.2` + 音频 `atempo=1.2`（不变尖、段间音色一致），时长约为原速 /1.2。

### 阶段三 · 封面
读 `references/03-cover.md`。以已确认满意的同系列封面为版式/形象锚点，用图像编辑只替换文字，分别出 16:9 横屏与 9:16 竖屏，回读核对无错别字、无旧产品名、形象未漂移。

## 配置

复制 `config.example.json` 为 `config.json`，填写 `pages[]`（每页图、所属配音段、口播稿、可选单独时长、精简字幕）、`voice_segments[]`、人声与 BGM 路径。所有相对路径相对 `project_dir`。

## 禁区

- 不要把整段口播逐句做成满屏字幕；不要让字幕压住卡片正文、数据或人物面部。
- 不要一次性生成超长 TTS 整稿；不要中途更换配音音色。
- BGM 音量不得盖过人声；不要用高饱和蓝紫。
- 封面形象每次保持同一角色，不要重绘成不同人；横竖版分别锁定比例，不拉伸。
- 改完 PPT 不得跳过服务端 lint 复核与逐页截图检查。
- 不要把 960×540 的在线截图直接放大当视频画面（会发虚）；视频源用 pptx 矢量渲染的 1080p 整页图，不要默认输出 720p。
