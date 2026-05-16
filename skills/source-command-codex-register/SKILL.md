---
name: source-command-codex-register
description: "批量注册 OpenAI Codex 账号（使用自有 Outlook 邮箱）。当用户说\"注册 codex\"、\"批量注册 openai\"、\"codex 注册\"或\"刷 codex 号\"时使用。"
---

# source-command-codex-register

Use this skill when the user asks to run the migrated source command `codex-register`.

## Command Template

# OpenAI Codex 批量注册

使用用户自有的 Outlook 邮箱批量注册 OpenAI Codex 账号。通过 IMAP 自动收取验证码。

## 脚本位置

```
/Users/whc/Downloads/codex-register1 2/main.py
```

## 工作流程

### 步骤 1：收集信息

依次向用户询问以下信息（用 AskUserQuestion 或对话）：

1. **邮箱列表文件路径** — 文件格式为一行一个邮箱地址，`#` 开头的行会被跳过
2. **注册数量** — 从文件前 N 个邮箱开始注册（输入 0 或"全部"表示用完文件里所有邮箱）
3. **代理地址** — 如 `http://127.0.0.1:7890`（必须用非 CN/HK 的代理）
4. **Outlook 邮箱密码** — 所有邮箱共用的密码，用于 IMAP 收验证码

### 步骤 2：确认信息

向用户确认：
- 邮箱文件路径和数量
- 代理地址
- 提醒：如果 Outlook 开了两步验证，需要用应用专用密码（https://account.live.com/proofs/AppPassword）
- 提醒：OpenAI 注册是无密码 OTP 模式，注册完成后通过 OAuth Token 登录

### 步骤 3：执行注册

确认后，构造并执行命令：

```bash
cd "/Users/whc/Downloads/codex-register1 2" && \
OUTLOOK_PASSWORD="<用户提供的密码>" \
python main.py \
  --emails "<邮箱文件路径>" \
  --count <数量> \
  --proxy "<代理地址>" \
  --yes
```

重要：
- 密码通过 `OUTLOOK_PASSWORD` 环境变量传递，不要写在命令行参数里
- 必须加 `--yes` 跳过交互确认（因为 Codex 的 Bash 不支持交互式输入）
- 脚本运行时间可能较长（每个邮箱需要等验证码），设置足够的 timeout

### 步骤 4：报告结果

脚本运行完后，向用户汇报：
- 成功/失败数量
- 每个邮箱的状态
- Token 文件保存位置

## 前置条件

脚本依赖需要安装：

```bash
cd "/Users/whc/Downloads/codex-register1 2" && pip install -r requirements.txt
```

## 注意事项

- 代理必须是非中国大陆/香港的 IP
- Outlook 如果开了两步验证，普通密码无法用于 IMAP，需要应用专用密码
- 每次注册之间有 5-20 秒随机间隔，避免被限流
- Token 文件默认保存在脚本目录下，文件名格式：`token_邮箱_时间戳.json`
