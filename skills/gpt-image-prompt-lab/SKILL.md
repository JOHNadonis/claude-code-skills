---
name: gpt-image-prompt-lab
description: 基于本地 GPT-Image-2 案例库，检索、改写、组合图像生成提示词。当用户说“帮我写图像 prompt”、“参考案例生成图片提示词”、“GPT-Image-2 prompt”、“改图提示词”、“广告图/海报/人像/UI mockup/角色设计 prompt”时使用。
autoActivate: false
---

# GPT Image Prompt Lab

用本地 `awesome-gpt-image-2-prompts` 案例库，为 GPT-Image-2 / OpenAI Images API 生成可直接使用的图像提示词。

核心原则：先匹配案例，再改写组合。不要凭空从零写，优先复用 references 中已经验证过的结构、风格词、负面词和场景描述。

---

## 本地资料

案例库位置：

```text
references/awesome-gpt-image-2-prompts/
```

重点文件：

```text
README.md                  # 英文总入口
README_zh-CN.md            # 中文总入口
cases/ecommerce.md         # 电商产品图
cases/ad-creative.md       # 广告创意
cases/portrait.md          # 人像摄影
cases/poster.md            # 海报插画
cases/character.md         # 角色设计
cases/ui.md                # UI / 社媒 mockup
cases/comparison.md        # 对比和社区案例
images/                    # 案例配图
data/                      # 结构化数据
LICENSE
```

---

## 触发条件

用户提出以下需求时使用：

- 写图像生成 prompt
- 参考案例改 prompt
- GPT-Image-2 / OpenAI Images API 图片提示词
- 生成广告图、海报、电商主图、人像摄影、角色设定、UI mockup、社媒图
- 改图提示词、image-to-image、背景替换、风格迁移、透明背景
- 需要 negative prompt、style keywords、shot description、composition

不要用于：

- 普通文字写作
- 代码生成
- 不涉及图像生成的设计咨询

---

## 工作流

### 1. 明确用户目标

如果信息足够，直接开始。缺少关键信息时最多问 2 个问题。

优先确认：

1. 图片用途：广告、电商、人像、海报、角色、UI、社媒、概念图
2. 主体：产品 / 人物 / 场景 / 品牌 / 物体
3. 风格：写实、电影感、极简、3D、插画、杂志、奢侈品、电商白底等
4. 输出约束：比例、是否留文字区、是否透明背景、是否要中文文字
5. 是否是改图：有参考图时输出 `Edit prompt`

### 2. 检索本地案例

根据用户意图读取最相关的 case 文件：

| 用户需求 | 优先读取 |
|---|---|
| 商品图、详情页、主图、包装图 | `cases/ecommerce.md` |
| 广告 KV、营销海报、品牌 campaign | `cases/ad-creative.md` |
| 人像、写真、摄影、证件/大片 | `cases/portrait.md` |
| 海报、插画、视觉艺术 | `cases/poster.md` |
| IP、头像、游戏角色、角色 sheet | `cases/character.md` |
| App 截图、网页 mockup、社媒卡片 | `cases/ui.md` |
| 不确定、想看多种玩法 | `cases/comparison.md` + `README.md` |

如果用户需求跨多个类型，读取 2-3 个相关文件并组合结构。

### 3. 抽取可复用结构

从案例里提取：

- 场景结构：主体 + 环境 + 动作 + 构图
- 视觉语言：lighting、lens、composition、material、texture
- 风格词：cinematic、editorial、photorealistic、3D render、minimalist 等
- 质量约束：high detail、natural skin texture、sharp focus 等
- 负面词：low quality、distorted features、extra limbs、blur、noise 等
- 改图语法：using uploaded image as reference、remove background、preserve identity 等

### 4. 生成结果

默认输出中文说明 + 英文 prompt。英文 prompt 通常更适合图像模型。

输出格式：

```markdown
## 推荐 Prompt

[英文完整 prompt]

## Negative Prompt

[负面提示词，必要时提供]

## 使用方式

- 文生图：直接把 Recommended Prompt 放进 prompt
- 图生图 / 改图：上传参考图后使用 Edit Prompt

## 可选变体

1. [更商业]
2. [更写实]
3. [更社媒传播]
```

如果用户明确要中文 prompt，可以输出中文，但保留关键风格词英文。

### 5. 改图场景

如果用户有参考图或说“把这张图改成...”，输出：

```markdown
## Edit Prompt

Using the uploaded image as the primary reference, [保留主体/身份/构图/产品细节] while changing [要改变的内容]. Preserve [不可改变项]. The final image should be [风格、光线、比例、用途].

## Negative Prompt

[避免身份漂移、产品变形、文字乱码、肢体错误等]
```

改图时必须明确：

- preserve 什么
- change 什么
- output style 什么
- avoid 什么

---

## Prompt 质量标准

好的图像 prompt 应该包含：

1. **主体明确**：谁 / 什么东西是画面中心
2. **场景明确**：在哪里，背景是什么
3. **构图明确**：近景、全身、俯拍、居中、三分法等
4. **光线明确**：softbox、golden hour、rim light、studio lighting 等
5. **材质和细节明确**：skin texture、fabric、glass、metal、packaging 等
6. **风格明确**：photorealistic、editorial、3D、minimal poster 等
7. **用途明确**：ad campaign、e-commerce hero image、social post、app mockup
8. **限制明确**：no text、transparent background、leave empty space for copy 等

---

## 常用输出模板

### 电商产品图

```text
Create a premium e-commerce hero image of [product], centered in the frame, photographed in a clean studio setup with [background/material]. Use soft diffused lighting, crisp product edges, realistic shadows, high-end commercial photography style, ultra-detailed materials, natural reflections, and a polished advertising look. Leave clean negative space for marketing copy. Aspect ratio [ratio].
```

### 广告创意

```text
Create a high-impact advertising visual for [brand/product/campaign]. The scene shows [main concept] with [symbolic elements], dramatic composition, cinematic lighting, premium color grading, sharp focus on the product, and a clear visual hierarchy. Designed as a modern campaign key visual, suitable for social media and outdoor ads.
```

### 人像摄影

```text
Create a cinematic editorial portrait of [person description], [pose/action], in [environment]. Use natural skin texture, shallow depth of field, soft highlights, realistic facial features, [lighting style], [lens/composition], photorealistic magazine photography, elegant color grading, emotionally expressive mood.
```

### 海报插画

```text
Create a striking poster illustration about [theme], featuring [main subject] in [composition]. Use bold visual hierarchy, refined color palette, graphic shapes, detailed atmosphere, balanced typography space, and a memorable central image. Style: [poster style].
```

### 角色设计

```text
Create a detailed character design sheet for [character], including front view, side view, back view, facial expression variations, outfit details, accessories, and color palette. The character should feel [personality], with consistent proportions, clean silhouette, production-ready concept art style.
```

### UI / 社媒 mockup

```text
Create a polished UI mockup for [app/product/page], displayed on [device/context]. The interface should show [key screens/components], clean spacing, modern typography, realistic device frame, subtle shadows, professional product presentation, and a high-end tech brand aesthetic.
```

---

## 使用示例

### 示例 1：广告图

用户：帮我给一个咖啡品牌写一条适合 GPT-Image-2 的广告图 prompt。

Codex：读取 `cases/ad-creative.md` 和 `cases/ecommerce.md`，生成广告 KV prompt、negative prompt 和 3 个风格变体。

### 示例 2：改图

用户：我上传一张产品图，帮我换成高端黑金背景。

Codex：输出 Edit Prompt，强调 preserve product shape, logo, label, proportions，change background and lighting，避免文字变形和产品失真。

### 示例 3：角色设定

用户：做一个赛博朋克猫咪侦探 IP 形象。

Codex：读取 `cases/character.md`，输出角色 sheet prompt，包括正侧背、表情、配件、色板和材质描述。
