# 阶段一：PPT 创作（飞书 Slides）

目标：产出一套分页清晰、每页带统一 logo、可逐页截图的讲解用 PPT。本阶段只负责“内容与排版”，视频在阶段二处理。

## 1. 分页结构（知识讲解类默认 7–9 页）

按“钩子 → 案例 → 概念 → 方法 → 要点 → 趋势/价值 → 行动清单 → 收尾”组织，每页只讲一个点：

1. 封面：标题 + 一句钩子，右下角/右上角放账号 logo
2. 真实案例（可选但推荐）：一个有数据的标杆案例（star 数、播放量、套数），关键事实用独立卡片条
3. 概念页：这个东西到底是什么，一句话定义
4. 核心方法页：全文最重要的方法论，放大处理
5. 要点页：补充规则/注意事项（引导问题、省 token 之类）
6. 趋势/价值页：它会替代什么、为什么现在值得做
7. 认知升级页：反常识判断（如 HTML 是模型母语）
8. 给普通人的起点：降低门槛
9. 收尾行动清单：三步行动 + 口播结束语

## 2. 统一品牌元素

- **每页右上角统一放账号圆形 logo**（AI观潮君），位置、尺寸全片一致。
- 配色克制：浅米白/浅蓝渐变底，深蓝黑粗体标题，蓝色短横线分隔，灰色小字卖点；不要高饱和蓝紫。
- 关键链接/仓库地址做成浅蓝底卡片条，配图标，不要直接糊一大段裸 URL 在正文里。

## 3. lark-cli 命令模板（飞书 Slides）

```bash
# 读取整份 XML，并查看服务端 lint 的 errors/warnings
lark-cli slides +xml-get --presentation <PID> --output ./final.xml --json

# 局部替换某一页（parts json 里用 block_replace / block_insert）
lark-cli slides +replace-slide --presentation <PID> --slide-id <SID> \
  --parts @parts.json --json

# 逐页截图（输出目录必须在当前工作目录或其下）
lark-cli slides +screenshot --presentation <PID> --slide-id <SID> --output-dir ./shots
```

parts.json 片段示例（卡片条 + 仓库地址）：

```json
[
  { "action": "block_replace", "block_id": "<现有block>",
    "replacement": "<shape type=\"text\" ...>...</shape>" },
  { "action": "block_insert",
    "insertion": "<shape type=\"rect\" ...><fill><fillColor color=\"rgba(224,231,255,1)\"/></fill></shape>" }
]
```

## 4. 改完必做的闭环（不要跳）

1. `+xml-get` 复核服务端 lint，要求 **0 error 0 warning**；有报错先修再继续。
2. 逐页 `+screenshot` 截图，肉眼检查文字是否溢出、logo 是否每页都在、卡片是否对齐。
3. 导出 pptx 留档：

```bash
lark-cli drive +export --token <PID> --doc-type slides --file-extension pptx \
  --output-dir ./out --file-name <名称> --overwrite --json
```

> 截图是阶段二视频的画面来源，务必导出清晰、比例统一的整页图。
