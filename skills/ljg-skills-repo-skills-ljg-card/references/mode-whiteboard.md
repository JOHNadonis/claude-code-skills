# 模具：白板（-w）

## 核心信条

**像站在白板前讲解一样，不是排版出来的。**

Whiteboard 的灵魂是"一个人拿着马克笔在白板上边讲边写"的现场感。标题大而粗、关键词用彩色笔圈出来、逻辑用箭头和框图串联、旁边有快速标注。和 Sketchnote 的区别：白板更结构化、更"讲解"、更干净，没有笔记本的私人感。

## 步骤 1：读取模板

Read `~/.claude/skills/ljg-card/assets/whiteboard_template.html`

模板提供：
- 马克笔字体加载（Permanent Marker + Kalam）
- CSS 变量（`--bg`, `--board`, `--ink`, `--red`, `--blue`, `--green`, `--orange`, `--marker-bg`）
- 微栅格底纹（白板磨砂面）
- 白板边框
- SVG 箭头 marker 定义（红/蓝/黑/绿四色）
- `.colophon` 署名栏
- `{{CUSTOM_CSS}}` 和 `{{CONTENT_HTML}}` 插槽

## 步骤 2：理解内容，选择风格

### 2.1 提取结构

从内容中提取：
- **核心论点**：一句话总结
- **3-8 个关键模块**：可以画成"区块"的东西
- **模块关系**：层级、因果、对比、并列
- **数据亮点**：适合大号数字展示的关键数据

### 2.2 选择风格路线

| 风格 | 视觉特征 | 触发信号 | 主色 |
|------|---------|---------|------|
| **架构图** | 大标题居左 + 层级方框 + 箭头连接 + 编号 | 系统/流程/步骤/架构类内容 | `--blue` 主导 |
| **脑暴墙** | 核心词居中 + 放射状分支 + 便签贴色块 + 关键词散落 | 发散型/多观点/创意/头脑风暴 | `--orange` 主导 |
| **Sprint 回顾** | 纵向时间线 + 里程碑节点 + 旁注 + 对比色标记 | 时间线/进程/回顾/对比类 | `--green` 主导 |
| **矩阵分析** | 2x2 或多格矩阵 + 象限标签 + 要素散布 | 分类/对比/评估/决策框架 | `--red` 主导 |

**选择原则**：
- 默认用「架构图」——最通用的白板风格
- 内容有多个并列观点/意见 → 脑暴墙
- 内容有时间/阶段维度 → Sprint 回顾
- 内容涉及分类/象限/对比 → 矩阵分析

## 步骤 3：设计画面

### 3.1 白板元素工具箱

**所有视觉元素用 CSS + SVG 实现，不用外部图片。**

#### 文字层级

| 层级 | 字体 | 字号 | 用途 |
|------|------|------|------|
| 主标题 | `--marker` (Permanent Marker) | 72-84px | 白板顶部大标题 |
| 模块标题 | `--hand` (Kalam) 700 | 48-56px | 各区块标题 |
| 正文 | `--hand` (Kalam) 400 | 34-40px | 说明文字 |
| 标注 | `--sans` (DM Sans) | 24-28px | 小字注释、数据 |
| 大号数字 | `--marker` | 72-120px | 数据亮点，抓眼球 |

**中文回退**：Permanent Marker 和 Kalam 对中文无效，自动回退到 PingFang SC。中文标题保持加粗，通过彩色马克笔效果（色块背景、粗下划线）维持白板感。

#### 马克笔效果（CSS 实现）

```css
/* 马克笔粗下划线 */
.underline-marker {
  border-bottom: 4px solid var(--red);
  padding-bottom: 2px;
}

/* 马克笔圈（强调关键词） */
.circled {
  border: 3px solid var(--red);
  border-radius: 45% 55% 50% 48%;
  padding: 4px 16px;
  display: inline-block;
}

/* 荧光笔高亮 */
.highlighted {
  background: var(--marker-bg);
  padding: 2px 8px;
}

/* 方框区块（白板上的框图） */
.box {
  border: 3px solid var(--ink);
  border-radius: 4px;
  padding: 20px 24px;
}

.box-blue { border-color: var(--blue); }
.box-red { border-color: var(--red); }
.box-green { border-color: var(--green); }

/* 虚线框 */
.box-dashed {
  border: 3px dashed var(--ink-light);
  border-radius: 4px;
  padding: 20px 24px;
}

/* 便签贴 */
.sticky {
  background: #FFF3BF;
  padding: 16px 20px;
  transform: rotate(-1deg);
  box-shadow: 2px 3px 8px rgba(0,0,0,0.06);
}

.sticky-blue { background: #DBEAFE; }
.sticky-green { background: #D1FAE5; }
.sticky-pink { background: #FCE7F3; }

/* 编号圆点 */
.num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px; height: 44px;
  border-radius: 50%;
  background: var(--blue);
  color: white;
  font: 700 24px var(--marker);
}
```

#### 连接箭头（SVG inline）

用 SVG path 画箭头。粗线（stroke-width: 3），搭配四色 marker-end。

### 3.2 布局原则

**白板是结构化的**——不像 sketchnote 那样自由散落，但也不是严格网格。

- **区块化**：内容分成 3-6 个明确区块，每块有框或色块底
- **层级清晰**：标题→子标题→正文，用字号+颜色拉开
- **箭头连接**：区块之间用箭头标注逻辑关系
- **留白适度**：比 sketchnote 更规整，但比长图更松散
- **色彩分区**：不同模块用不同马克笔颜色标记

### 3.3 画面构成（按风格）

#### 架构图
```
[大标题 - 蓝色粗体] 居左
═══════════════════════
│                      │
│  ┌──────┐  ┌──────┐  ┌──────┐
│  │模块1 │→│模块2 │→│模块3 │
│  │      │  │      │  │      │
│  └──────┘  └──────┘  └──────┘
│      ↓          ↓         ↓
│  说明文字    说明文字   说明文字
│
│  [底部总结 - 红色框]
```

#### 脑暴墙
```
       [便签1]   [便签2]
            \     /
     [便签3] → [核心词] ← [便签4]
            /     \
       [便签5]   [便签6]

  底部：关键 takeaway，红色下划线
```

#### Sprint 回顾
```
  [标题]

  ●──────●──────●──────●──────●
  阶段1   阶段2   阶段3   阶段4   阶段5
  │       │       │       │       │
  注释    注释    注释    注释    注释
```

#### 矩阵分析
```
  [标题]
            │ 维度A高
    ────────┼────────
    象限1   │ 象限2
            │
    ────────┼────────
    象限3   │ 象限4
            │ 维度A低
   维度B低       维度B高
```

## 步骤 4：写 CSS + HTML

所有 CSS 写入 `{{CUSTOM_CSS}}`。所有 HTML 写入 `{{CONTENT_HTML}}`。

**CSS 从零写**——class 名反映内容语义，不是通用名。

替换变量：

| 变量 | 内容 |
|------|------|
| `{{CUSTOM_CSS}}` | 这张图的全部 CSS（包括覆盖 :root 变量） |
| `{{CONTENT_HTML}}` | 这张图的全部 HTML |
| `{{SOURCE}}` | 署名 |
| `{{ARXIV_LINE}}` | arxiv 时填入，否则空 |

写入：`/tmp/ljg_cast_whiteboard_{name}.html`

## 步骤 5：自检

- [ ] 一眼看上去像白板上写的吗？如果像普通排版，重做
- [ ] 有没有至少用到 2 种马克笔颜色？
- [ ] 有没有方框/箭头连接不同区块？
- [ ] 标题是否够大够粗（≥ 72px）？
- [ ] 和 sketchnote 放在一起能一眼区分吗？（无点阵、无手绘简笔画、更结构化）
- [ ] 正文手写字体 ≥ 34px？标注 ≥ 24px？
- [ ] 内容区块是否有明确的视觉边界？
- [ ] 数据/关键数字是否用大号或彩色突出？

## 步骤 6：截图

```bash
node ~/.claude/skills/ljg-card/assets/capture.js /tmp/ljg_cast_whiteboard_{name}.html ~/Downloads/{name}.png 1080 800 fullpage
```
