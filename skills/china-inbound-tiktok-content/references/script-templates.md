# 脚本模板：四种生产形式

> 模式 A 写脚本时按用户选择的形式读对应章节。所有旁白/字幕为英文，分镜说明为中文。
> 通用节奏律：**30-45 秒最优**（攻略类可到 60-90 秒），每 3-5 秒一个新信息点或画面切换。

## 形式 1：素材混剪 + 英文配音/字幕（默认主力）

### 分镜表模板

| 时间轴 | 画面（b-roll） | 英文旁白 VO | 屏幕字幕 |
|--------|---------------|------------|----------|
| 0-3s | [最炸裂画面] | [Hook] | [大字结论] |
| 3-8s | [背景铺垫] | [Setup：一句话立题] | [关键词] |
| 8-Xs | [价值点1画面] | [Beat 1] | [数字/要点] |
| ... | [价值点2-4] | [Beat 2-4] | ... |
| 尾3-5s | [人设镜头/logo] | [Payoff + CTA] | [CTA 文字] |

### 结构要求
- **Hook(0-3s) → Setup(3-8s) → 3-5 个 Beat → Payoff → CTA**，Beat 之间用画面硬切不用转场特效
- VO 语速按 2.5 词/秒估算时长；写完数一遍词数标注总时长
- 每个 Beat 在素材清单里给出 2-3 个候选画面描述，方便剪辑找料

### 素材来源建议（写进素材清单）
- 自拍素材 > 授权素材站（Pexels/Pixabay 有中国城市 b-roll）> 向拍摄者购买授权
- 不要直接搬运他人 TikTok/YouTube 视频，平台查重会限流

### 配音建议
- TTS 选美音自然款（ElevenLabs 类），语气"朋友分享"不要"纪录片解说"
- 字幕全程烧录，大量观众静音刷

## 形式 2：真人出镜口播

### 提词稿模板

```
[镜头：怼脸近景，第一句抛 hook]
HOOK: ...

[镜头：切中景或走动，降低疲劳]
SETUP: One sentence — why should you care.

BODY（3 个 point，每个 = 断言 + 证据/例子 + 一句转场）:
Point 1: ...
Point 2: ...
Point 3: ...

[镜头：回怼脸]
PAYOFF: 一句话总结 + 情绪落点
CTA: "Follow for part 2" / "Comment GUIDE and I'll send you..."
```

### 口播专属规则
- 每句 ≤ 15 词，写完朗读一遍，拗口就改
- 每 8-10 秒设计一次 pattern interrupt：镜头推近/道具入画/字幕爆闪/B-roll 插入，脚本里用 [PI: 描述] 标注
- 讲攻略时手持实物（护照/手机展示 app 界面）比纯说强 3 倍

## 形式 3：AI 生成视频

### 交付格式：分场景 prompt 表

| 场景 | 时长 | 视频生成 Prompt（英文） | VO |
|------|------|------------------------|-----|
| 1 | 5s | [镜头语言+主体+环境+光线+运动] | [对应旁白] |

### Prompt 写作要点
- 每段 prompt 包含：镜头类型（aerial/POV/tracking shot）+ 主体动作 + 环境细节 + 光线氛围 + 画幅 9:16
- 示例："POV tracking shot walking through a neon-lit night market in Chongqing, steam rising from food stalls, crowds, rain-slicked streets reflecting red lanterns, cinematic, vertical 9:16"
- **AI 视频的合规位**：适合做"想象中 vs 现实"的想象侧、地图动画、未来感概念画面；**不要用 AI 画面冒充实拍**（观众识破即掉信任，评论区会翻车）——实拍感内容还是用真素材
- 可衔接 seedance / seedance-director skill 生成

## 形式 4：图文帖（Photo Mode）

### 逐页模板（6-10 页）

```
Page 1（封面）: 大字标题 = hook（如 "7 DAYS IN CHINA UNDER $800"）+ 最强一张图
Page 2: 立题/痛点确认（"Here's the exact route + costs"）
Page 3-N: 每页一个要点，图 + ≤30 词文字，数字加粗
最后一页: 总结 + CTA（"Save this 📌 / Comment GUIDE for the full PDF"）
```

### 图文专属规则
- 图文帖收藏率天然高，最适合攻略/清单/行程类选题（支柱 4、5、7）
- 每页文字手机上要 2 秒读完；信息密度高的放中间页（前 2 页决定翻页率）
- 生产成本最低，日历排期里用它填产能空档、维持日更

## 通用：Caption 之外的"三层文案"

每条内容其实有三层文案，脚本交付时都要给：
1. **视频内文案**：VO + 烧录字幕（上面模板）
2. **Caption**：见 `hashtag-cta-conversion.md` 的 SEO 写法
3. **评论区预埋**：发布后 5 分钟内自己发的置顶评论（互动引子或 lead magnet 入口）
