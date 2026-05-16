<div align="center">

# 女娲.skill

> *「你想蒸馏的下一个员工，何必是同事」*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![Skills](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh)

<br>

**女娲帮你蒸馏任何人的思维方式，让马斯克、纳瓦尔、芒格、费曼都给你打工。**

<br>

[同事.skill](https://github.com/titanwings/colleague-skill) 证明了蒸馏一个人是可行的。<br>
那何必蒸馏同事？去蒸馏芒格、费曼、马斯克。<br>
只需输入一个名字，女娲自动完成调研、提炼、验证全流程。

[看效果](#效果示例) · [安装](#安装) · [它蒸馏了什么](#女娲蒸馏了什么) · [工作原理](#工作原理)

<br>

**其他语言 / Other Languages:**

[English](README_EN.md) · [日本語](README_JA.md) · [한국어](README_KO.md) · [Español](README_ES.md)

</div>

---

## 效果示例

```
用户      ❯ 我同时想做自媒体、写书、做独立开发，精力完全不够

Naval     ❯ 你列了三个欲望。每个欲望都是你跟不快乐签的一份合同。
            不是精力不够，是合同太多。
            
            问你自己：哪一个做起来你会忘记时间？
            那个就是你的特定知识所在。
            
            不是三选一。是先一，再一，再一。
            串行复利，不是并行内耗。
```

```
用户      ❯ 我们的SaaS产品获客成本太高了

马斯克     ❯ 先别想怎么降。先算物理极限。
            获客的最小必要动作是什么？用户从知道你到付费，
            信息传递的理论最短路径是什么？
            
            现在你的实际路径是理论路径的几倍？
            如果超过3倍，中间一定有可以砍掉的步骤。
            不是优化漏斗，是质疑漏斗本身该不该存在。
```

再来一个大家更熟悉的。蒸馏张雪峰之后：

```
用户      ❯ 家里条件一般，孩子想学金融，去不了顶尖学校，该不该报？

张雪峰    ❯ 千万别报。我说过多少遍了，金融不是你学出来的，金融是
            你爹妈给你带出来的。顶尖学校的金融，人家同学是行长的
            儿子、基金经理的女儿，人脉就是资源。你普通家庭去个普通
            学校学金融，毕业出来干什么？卖保险、跑银行柜台、做电销。
            先谋生再谋爱，家里没矿就选技术类专业，学个硬本事，靠
            自己吃饭。金融这碗饭，不是谁都端得起的。
```

这不是角色扮演。Naval用的是他的「欲望即合同」心智模型，马斯克用的是「渐近极限法」，张雪峰用的是「ROI教育观」和「阶层流动现实主义」。**它们不是在复读名人语录，是在用名人的认知框架帮你分析。**

---

## 安装

```bash
npx skills add alchaincyf/nuwa-skill
```

然后在 Claude Code 里：

```
> 蒸馏一个保罗·格雷厄姆
> 造一个张小龙的视角Skill
> 帮我做一个段永平的Skill
```

造完之后直接调用：

```
> 用芒格的视角帮我分析这个投资决策
> 费曼会怎么解释量子计算？
> 切换到Naval，我在纠结三件事
```

---

## 女娲蒸馏了什么

蒸馏各领域最强的人，需要提取比日常工作习惯更深的东西。女娲提取六层：

| 层次 | 说明 |
|---|---|
| **怎么说话** | 表达DNA——语气、节奏、用词偏好 |
| **怎么想** | 心智模型、认知框架 |
| **怎么判断** | 决策启发式 |
| **什么不做** | 反模式、价值观底线 |
| **知道局限** | 诚实边界 |

工作习惯可以靠流程文档传递，但让芒格和马斯克面对同一个问题做出不同判断的，是认知框架。女娲提取的是认知操作系统。

### 诚实边界

每个Skill都明确标注做不到什么：

- 蒸馏不了直觉——框架能提取，灵感不能
- 捕捉不了突变——截止到调研时间的快照
- 公开表达 ≠ 真实想法——只能基于公开信息

**一个不告诉你局限在哪的Skill，不值得信任。**

---

## 工作原理

输入一个名字后，女娲做四件事：

**1. 六路并行采集**——著作、播客/访谈、社交媒体、批评者视角、决策记录、人生时间线，6个Agent同时跑，各自存档。

**2. 三重验证提炼**——一个观点要被收录为心智模型，必须：跨2+个领域出现过（不是随口一说）、能推断对新问题的立场（有预测力）、不是所有聪明人都会这么想（有排他性）。三个都过才收录。

**3. 构建Skill**——3-7个心智模型 + 5-10条决策启发式 + 表达DNA + 价值观与反模式 + 诚实边界，写入SKILL.md。

**4. 质量验证**——拿3个此人公开回答过的问题测试，方向一致才通过。再用1个他没讨论过的问题测试，Skill应该表现出适度不确定而非斩钉截铁。

完整方法论在 `references/extraction-framework.md`。

---

## 仓库结构

```
nuwa-skill/
├── SKILL.md                    # 女娲本体
├── references/
│   ├── extraction-framework.md # 提炼方法论（想深入了解看这个）
│   └── skill-template.md       # 生成Skill的模板
└── examples/
    ├── naval-perspective/       # Naval 完整示例 + 调研数据
    └── elon-musk-perspective/   # 马斯克 完整示例 + 调研数据
```

调研过程全透明。examples里有完整的调研文件，你可以看到信息怎么被收集、筛选、变成心智模型。

---

## 背后的故事

[同事.skill](https://github.com/titanwings/colleague-skill) 最近在GitHub爆火——把离职同事蒸馏成AI Skill，几天破5000星。它证明了一件事：蒸馏一个人是完全可行的。

既然我们有了蒸馏人的能力，为什么只蒸馏身边的同事？去蒸馏各领域最强的人。而且幸运的是，这些人通常留下了大量可以被蒸馏的材料——著作、演讲、访谈、社交媒体。这是对自己能力的极大补充。

我之前就一直在做类似的事，但蒸馏的不是同事，是芒格、费曼、Naval、马斯克、塔勒布这些人。今天把方法论开源了。

女娲不复制人。它提取认知操作系统。

**女娲（Nuwa）**，中国神话里用泥土造人的女神。这里的泥土是公开信息，造出来的不是人，是一面镜子。

---

## Star History

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=alchaincyf/nuwa-skill&type=Date)](https://star-history.com/#alchaincyf/nuwa-skill&Date)

</div>

---

## 关于作者

花叔/花生，AI Native Coder，独立开发者。所有产品都是AI写的代码（[小猫补光灯](https://apps.apple.com/app/id6738028637)登顶中国App Store付费榜第一）。Claude Code里跑着40+个自定义Skill，女娲是造Skill的Skill。

- 公众号：花叔
- X：[@AlchainHust](https://x.com/AlchainHust)
- B站：[AI进化论-花生](https://space.bilibili.com/14097567)
- YouTube：[@Alchain](https://www.youtube.com/@Alchain)

## 许可证

MIT — 随便用，随便改，随便造。

---

<div align="center">

**同事.skill** 蒸馏了人做什么。<br>
**女娲** 蒸馏了人怎么想。<br><br>
*你想蒸馏的下一个员工，何必是同事。*

<br>

MIT License © [花叔 Huashu](https://github.com/alchaincyf)

</div>

---

## English

> *"The next person you want to distill doesn't have to be a colleague."*

**[colleague-skill](https://github.com/titanwings/colleague-skill)** proved that distilling a person into an AI skill is viable. **Nuwa** asks: why stop at colleagues? Distill the best minds in every field — Munger, Feynman, Musk, Naval — people who conveniently left mountains of distillable material behind.

Nuwa is a Claude Code skill that extracts cognitive frameworks — mental models, decision heuristics, expression DNA — from any public figure into a runnable perspective skill.

Not role-playing. Cognitive architecture extraction.

**Install**: `npx skills add alchaincyf/nuwa-skill`

**How it works**: Input a name → 6 parallel research agents → 40+ primary sources → triple-verified mental models → quality-validated SKILL.md

**Examples included**: Naval Ravikant and Elon Musk with full research data.

See the Chinese README above for live examples and methodology.
