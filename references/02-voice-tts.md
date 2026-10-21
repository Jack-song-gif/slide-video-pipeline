# 阶段二：配音、时间线、字幕与成片

## 1. 配音（TTS）分段规则——最容易踩的坑

文生语音单条有上限（约 120s），**整段长稿一次性生成会被静默截断**，结尾丢失。正确做法：

1. 把全稿按语义切成若干段，每段控制在 ~90s 以内，宁短勿长。
2. 逐段单独生成 wav，下载到 `audio/`。
3. 用 `scripts/concat_voice.py` 本地 concat 成完整 `voice.wav`，并回读每段实测时长。

配音气质（知识讲解/口播）：亲切自然、语速轻快，像和观众聊天；不要播音腔。男声用标准短视频青年男声即可，女声选温暖元气女声；音色全片统一，中途不要换。

## 2. 时间线分配

`scripts/make_timeline.py`：

- 某页单独 TTS 时，把实测秒数填进 `pages[i].voice_duration`，最准；
- 否则按 segment 分组，组内按口播字数权重（中文 1.0、ASCII 0.55）摊分该段实测时长；
- 每页展示时长 = 朗读时长 + gap（默认 0.9s），给切镜留呼吸。

## 3. 字幕原则：只放关键信息，不遮画面

- **每页一条标题式精简关键字幕**，不是逐句口播字幕。整句搬上屏会挡住卡片正文和人物。
- 字幕用半透明深色底条（`BorderStyle=4`），压在卡片下沿与底部结论条之间的空隙；`MarginV` 按当前分辨率微调，宁可留白也不要压字。
- 默认不开逐句同步字幕；只有用户明确要求时才做。

## 4. BGM

- 选轻快治愈、无人声的纯音乐，循环铺底。
- 音量压到 `bgm_volume=0.12` 左右，只垫底，绝不盖过人声。
- 人声 `apad` 兜底到全长，`amix` 取最长时长。

## 5. 执行顺序

前提：`pages[].image` 已指向阶段一用 `export_highres_pages.ps1` 渲染的 1920×1080 高清整页图，config.video 默认 1920×1080 / crf16 / preset slow。

```bash
python scripts/concat_voice.py  --config config.json   # 拼人声、回读时长
python scripts/make_timeline.py --config config.json   # 算时长、出 sub.srt/timeline.json
python scripts/build_segments.py --config config.json  # 高清页图→带淡入淡出的画面
python scripts/mix_render.py   --config config.json    # 烧字幕(优先sub.ass)+混音出成片
python scripts/check_volume.py --config config.json    # 核验响度
```

## 6. 成片验收

- 分辨率 1920×1080；逐页抽帧：文字锐利不发虚、不溢出、logo 在、字幕不遮正文/人物。
- `check_volume.py`：mean_volume 约 -30~-20 dB，max_volume 不高于 -3 dB；爆音就限幅人声，而不是继续压 BGM。
- 总时长与 timeline.json 的 video_dur 一致。
- 可选 1.2x 保调版：`setpts=PTS/1.2` + `atempo=1.2`，时长≈原速/1.2，音色不变尖。
