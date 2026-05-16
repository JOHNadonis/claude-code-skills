---
name: ask-codebase-questions
description: Turn an open-source repository URL or local codebase into beginner-friendly codebase learning questions, guided reading paths, and concrete prompts. Use when the user sends a GitHub/GitLab/source repository link or issue/PR link and asks to learn, study, understand, onboard, read the code, ask codebase questions, find beginner questions, explain a class/function/module, understand Git history/design decisions, or asks in Chinese phrases like “学习这个项目”, “新手该问什么”, “问代码库问题”, “看懂这个仓库”.
---

# Ask Codebase Questions

## Overview

Help the user learn a codebase by turning a repository into a map of good beginner questions. Prefer concrete, code-grounded questions over generic advice.

## Workflow

1. Identify the target:
   - Parse the repository, issue, PR, branch, or file URL.
   - Prefer an existing local checkout if present; otherwise inspect the remote and clone/read only what is needed.
   - If the user only sends a repo link plus “learn/study/understand”, proceed without asking a clarification question.

2. Build a quick codebase map:
   - Read `README`, `docs/`, `CONTRIBUTING`, package manifests, config files, and tests.
   - Use `rg --files`, package scripts, and top-level directories to identify entrypoints, modules, and boundaries.
   - Check recent commits and issue/PR context when the user asks “why was this designed this way?”

3. Produce a beginner question map:
   - Start with questions that help the user run, locate, and trace the system.
   - Include file-specific questions tied to real classes, functions, commands, modules, tests, or issues.
   - Group questions by learning value, not by directory dump.

4. Answer or guide:
   - If the user asks for questions, give categorized questions they can ask next.
   - If the user asks one concrete question, answer it with a simple mental model, the relevant call path, and file references.
   - If the user asks for a learning path, give a short sequence: run it, trace one feature, read one data flow, then make one safe change.

## Question Categories

Use these categories selectively:

- **Orientation**: What problem does this repo solve? What is the smallest runnable path? Which files are entrypoints?
- **Architecture**: What are the main modules? Which module owns state, IO, networking, persistence, or UI?
- **Call Path**: What happens from command/API/user action X to the final side effect?
- **Class/Function Use**: Who constructs this class? Who calls this function? What invariant do its parameters encode?
- **Data Flow**: Where does data enter, transform, persist, and leave?
- **Configuration**: Which environment variables, config files, or feature flags change behavior?
- **Errors And Edge Cases**: What failures are expected? Where are retries, fallbacks, validation, or cleanup handled?
- **Tests**: Which tests best explain expected behavior? What tiny test should a beginner run or modify first?
- **Git History**: Which commits introduced this design? What changed before/after, and what tradeoff does that imply?
- **Issues And PRs**: What user pain or design debate does an issue/PR reveal? Which files did it touch?
- **Good First Change**: What small docs/test/CLI/parser/refactor change would teach the system without high risk?

## Output Patterns

For a repo-level learning request, use this shape:

```markdown
**Repository Map**
Short summary of purpose, stack, and main packages/modules.

**Best Beginner Questions**
1. ...
2. ...

**First Learning Route**
1. Run/read ...
2. Trace ...
3. Change/test ...
```

For a specific symbol or file:

```markdown
**Mental Model**
What this symbol does in plain language.

**Where It Is Used**
Callers, tests, commands, or runtime entrypoints.

**Why It Looks This Way**
Parameter/state/design rationale, using code and history when available.

**Next Questions**
Questions the user should ask next.
```

## Guidelines

- Respond in the user's language; keep code identifiers, commands, file names, and commit messages in English.
- Keep the tone beginner-friendly without diluting technical accuracy.
- Prefer 10-25 high-signal questions over exhaustive lists.
- Include concrete file paths or URLs whenever possible.
- Ask at most one clarification question, only when the target repo or learning goal is genuinely ambiguous.
- Do not run untrusted install/build scripts just to generate beginner questions unless the user asks for runtime verification.
- When history or issue context is incomplete, state the limit and label inferences clearly.
