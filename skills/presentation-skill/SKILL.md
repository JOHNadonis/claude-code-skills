---
name: presentation-skill
description: 演讲脚本 + PPT 一键生成器。输入主题自动生成演讲稿和可播放的 HTML 幻灯片（支持点击/自动播放、键盘控制、导出 PDF）。使用 awesome-design-md 62 种品牌级设计风格。触发词："/ppt"、"做PPT"、"演讲稿"、"presentation"、"幻灯片"、"做个演示"
---

# Presentation — 演讲脚本 + PPT 一键生成

输入一个主题，自动生成演讲脚本和品牌级设计质感的 HTML 幻灯片。支持 62 种世界级品牌设计风格，一键切换。

## 触发词

- "/ppt"
- "做PPT"
- "做个PPT"
- "演讲稿"
- "presentation"
- "幻灯片"
- "做个演示"
- "演示文稿"

## 输入

| 参数 | 必须 | 说明 |
|------|------|------|
| **主题** | 是 | 演讲/演示的主题 |
| **风格** | 否 | 设计风格名称（不指定则引导选择） |
| **时长** | 否 | 目标演讲时长，默认 10 分钟 |
| **语言** | 否 | 脚本语言，默认中文 |
| **页数** | 否 | 幻灯片页数，默认根据时长自动计算（约 1 页/分钟） |

## 工作流程

```
引导选风格 → 生成演讲脚本 → 设计幻灯片 → 输出 HTML → 浏览器预览
```

---

### Step 1：引导用户选择设计风格

如果用户未指定风格，展示风格选择菜单。按场景分类推荐：

```
🎨 请选择你喜欢的 PPT 设计风格：

━━━ 科技 / AI ━━━
 1. Codex     — 温暖陶土色调，学术优雅
 2. vercel     — 极简黑白，Geist 字体
 3. linear     — 超精简紫色调，专业感
 4. stripe     — 标志性紫色渐变，精致
 5. nvidia     — 绿黑能量感，技术力量
 6. spacex     — 纯黑白未来主义

━━━ 商务 / 企业 ━━━
 7. apple      — 苹果级留白，极致优雅
 8. notion     — 温暖极简，知识感
 9. ibm        — 企业级蓝色系统
10. superhuman — 高端暗色，键盘优先
11. hashicorp  — 企业级黑白清洁

━━━ 创意 / 设计 ━━━
12. figma      — 多彩活泼，专业中带趣味
13. framer     — 大胆黑蓝，运动感
14. airbnb     — 温暖珊瑚色，摄影驱动
15. spotify    — 鲜绿暗色，大胆排版
16. nike       — 黑白对比，全大写 Futura

━━━ 金融 / 数据 ━━━
17. coinbase   — 信赖蓝，机构感
18. revolut    — 暗色渐变卡片，金融精确
19. binance    — 币安黄+黑，交易桌紧迫感

━━━ 汽车 / 奢华 ━━━
20. ferrari    — 明暗对比，法拉利红点缀
21. tesla      — 极简摄影，激进减法
22. lamborghini — 纯黑+金色，奢华感
23. bmw        — 暗色精密，德式工程美学

输入编号或名称即可，也可以说"帮我选"让我根据主题推荐。
```

**智能推荐**：如果用户说"帮我选"，根据主题自动匹配：
- 技术分享 → vercel / linear / Codex
- 产品发布 → apple / stripe / framer
- 商业提案 → notion / ibm / superhuman
- 创意展示 → figma / airbnb / spotify
- 数据报告 → coinbase / posthog / sentry
- 教育培训 → Codex / notion / mintlify

### Step 2：获取设计规范

根据用户选择的风格，从 awesome-design-md 仓库获取对应的 DESIGN.md：

```
https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/designs/{slug}/DESIGN.md
```

从 DESIGN.md 中提取以下关键设计变量：

| 要素 | 用途 |
|------|------|
| **配色系统** | CSS 变量定义（primary, accent, surface, text 等） |
| **字体层级** | 标题/正文/标注的 font-family, size, weight, line-height |
| **阴影系统** | 卡片/按钮的 box-shadow 层级 |
| **圆角规范** | border-radius 体系 |
| **间距规范** | spacing scale |

### Step 3：生成演讲脚本

根据主题和时长，生成结构化演讲脚本：

```markdown
# 演讲脚本：{主题}

预计时长：{N} 分钟
幻灯片数：{M} 页

---

## 第 1 页 — 开场（封面）
**幻灯片内容**：标题 + 副标题 + 演讲者
**演讲词**：
> （此处是完整的口语化演讲词，自然、有感染力，不是干巴巴的要点罗列）

**时长**：1 分钟
**提示**：[开场节奏建议、肢体语言提示]

---

## 第 2 页 — 问题引入
**幻灯片内容**：一个引人思考的问题/数据
**演讲词**：
> ...

...以此类推
```

**脚本质量要求**：
- 演讲词必须是**完整的口语句子**，不是关键词列表
- 开头要有**钩子**（故事/数据/提问），不要自我介绍开场
- 每页有**一个核心观点**，不堆砌
- 转场自然，页与页之间有过渡句
- 结尾有**行动号召**（CTA）

### Step 4：生成 HTML 幻灯片

生成一个**单文件** HTML，包含完整的幻灯片播放器。

#### 4.1 整体结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{演讲标题}</title>
  <!-- Google Fonts（根据 DESIGN.md 指定的字体） -->
  <link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
  <style>
    /* === 设计系统变量（来自 DESIGN.md） === */
    :root { ... }
    /* === 幻灯片引擎样式 === */
    /* === 幻灯片内容样式 === */
    /* === 控制栏样式 === */
    /* === 打印/PDF 样式 === */
  </style>
</head>
<body>
  <!-- 幻灯片容器 -->
  <div class="slides-container">
    <div class="slide active" data-index="0">...</div>
    <div class="slide" data-index="1">...</div>
    ...
  </div>
  <!-- 控制栏 -->
  <div class="controls">...</div>
  <!-- 演讲者备注面板 -->
  <div class="speaker-notes">...</div>
  <script>/* 播放引擎 */</script>
</body>
</html>
```

#### 4.2 幻灯片引擎（JavaScript）

必须实现以下功能：

**导航控制**：
```javascript
// 键盘控制
document.addEventListener('keydown', (e) => {
  switch(e.key) {
    case 'ArrowRight':
    case 'ArrowDown':
    case ' ':          // 空格
    case 'Enter':
      nextSlide(); break;
    case 'ArrowLeft':
    case 'ArrowUp':
      prevSlide(); break;
    case 'f':
    case 'F':
      toggleFullscreen(); break;
    case 'a':
    case 'A':
      toggleAutoplay(); break;
    case 'n':
    case 'N':
      toggleNotes(); break;
    case 'Escape':
      exitFullscreen(); break;
    case 'p':
    case 'P':
      exportPDF(); break;
  }
});

// 点击控制：点击幻灯片右半边 → 下一页，左半边 → 上一页
// 触摸滑动：支持移动端左右滑动切换
```

**自动播放**：
```javascript
let autoplayInterval = null;
let autoplaySpeed = 5000; // 默认 5 秒/页

function toggleAutoplay() {
  if (autoplayInterval) {
    clearInterval(autoplayInterval);
    autoplayInterval = null;
    updateAutoplayButton('▶ Auto');
  } else {
    autoplayInterval = setInterval(nextSlide, autoplaySpeed);
    updateAutoplayButton('⏸ Pause');
  }
}
```

**全屏模式**：
```javascript
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
}
```

**PDF 导出**：
```javascript
function exportPDF() {
  // 显示所有幻灯片用于打印
  document.body.classList.add('print-mode');
  window.print();
  document.body.classList.remove('print-mode');
}
```

#### 4.3 控制栏 UI

底部控制栏（非全屏时可见，全屏时悬停底部显示）：

```
┌────────────────────────────────────────────────────┐
│  ◀  │  3 / 12  │  ▶  │  ▶ Auto  │  ⛶ Full  │  📥 PDF  │  📝 Notes  │
└────────────────────────────────────────────────────┘
```

- **进度条**：页码指示器 + 可点击的进度条
- **自动播放按钮**：切换自动播放，显示当前状态
- **全屏按钮**：进入/退出全屏
- **PDF 按钮**：触发打印/导出 PDF
- **备注按钮**：显示/隐藏演讲者备注

控制栏样式使用当前设计风格的 accent 色。

#### 4.4 幻灯片切换动画

默认使用淡入滑动效果：

```css
.slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transform: translateX(30px);
  transition: opacity 0.5s ease, transform 0.5s ease;
  pointer-events: none;
}

.slide.active {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

.slide.prev {
  opacity: 0;
  transform: translateX(-30px);
}
```

#### 4.5 打印 / PDF 样式

```css
@media print {
  /* 打印模式：每页一张幻灯片 */
  .controls, .speaker-notes, .download-bar { display: none !important; }

  .slides-container {
    position: static;
    overflow: visible;
  }

  .slide {
    position: relative !important;
    opacity: 1 !important;
    transform: none !important;
    pointer-events: auto !important;
    page-break-after: always;
    width: 100vw;
    height: 100vh;
    display: flex !important;
    align-items: center;
    justify-content: center;
  }
}
```

#### 4.6 幻灯片内容设计原则

每张幻灯片的内容遵循以下设计原则：

**文字极简**：
- 标题：最多 1 行
- 内容：最多 3-5 个要点，每个要点一行
- 绝不放大段文字，演讲词放在备注里

**视觉层级清晰**：
- 大标题突出核心观点
- 数字/数据用超大字号呈现
- 图标使用 emoji 或 SVG inline，不依赖外部图片

**常用页面类型**：

| 类型 | 布局 | 适用场景 |
|------|------|----------|
| **封面** | 居中大标题 + 副标题 + 演讲者 | 第 1 页 |
| **章节页** | 居中章节标题 + 装饰元素 | 章节分隔 |
| **观点页** | 大字号核心观点 + 小字补充 | 关键论点 |
| **列表页** | 标题 + 3-5 条要点（带图标） | 罗列要点 |
| **数据页** | 超大数字 + 说明文字 | 数据冲击 |
| **对比页** | 左右/上下两栏对比 | Before/After |
| **引用页** | 大段引言 + 出处 | 名言/用户反馈 |
| **CTA 页** | 行动号召 + 联系方式 | 结尾 |

#### 4.7 演讲者备注面板

侧边滑出面板，显示当前页的完整演讲词：

```css
.speaker-notes {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 350px;
  transform: translateX(100%);
  transition: transform 0.3s ease;
  background: rgba(0,0,0,0.95);
  color: #fff;
  padding: 24px;
  overflow-y: auto;
  z-index: 1000;
}

.speaker-notes.open {
  transform: translateX(0);
}
```

#### 4.8 响应式适配

```css
/* 幻灯片容器保持 16:9 比例 */
.slides-container {
  width: 100vw;
  height: 100vh;
  max-width: 1920px;
  max-height: 1080px;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
}

/* 内容自适应缩放 */
.slide {
  padding: 60px 80px;
}

@media (max-width: 768px) {
  .slide { padding: 30px 40px; }
  .slide h1 { font-size: 2em; }
  .controls { font-size: 14px; }
}
```

### Step 5：输出与交付

1. **演讲脚本**保存为 `{主题}_演讲脚本.md`
2. **HTML 幻灯片**保存为 `{主题}_slides.html`
3. 两个文件都保存到**用户当前工作目录**
4. 用 `open {主题}_slides.html` 在浏览器中预览
5. 告知用户操作方式：

```
✅ 演讲脚本和幻灯片已生成！

📄 演讲脚本：{主题}_演讲脚本.md
🎬 HTML 幻灯片：{主题}_slides.html（已在浏览器中打开）

操作指南：
  → / ← / Space    翻页
  F                 全屏
  A                 自动播放（5秒/页）
  N                 显示演讲者备注
  P                 导出 PDF（浏览器打印）
  点击右半屏         下一页
  点击左半屏         上一页

需要调整内容、风格或页数吗？
```

## 风格获取失败的降级方案

如果无法从 GitHub 获取 DESIGN.md：

1. 使用内置的通用设计变量（基于 Stripe 风格的中性渐变方案）
2. 告知用户获取失败，已使用默认风格
3. 默认配色：深色背景 `#0a0a0a`，白色文字，渐变 accent

## 注意事项

- HTML 是**单文件**，不依赖本地资源
- 外部依赖仅限：Google Fonts CDN
- 幻灯片保持 **16:9** 比例
- 每页内容**极简**，详细内容放演讲者备注
- 动画轻量，不卡顿
- 打印 PDF 时隐藏所有控制元素
- 如果主题是英文，脚本默认用英文；中文主题默认中文
