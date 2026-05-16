#!/usr/bin/env python3
"""
设置脚本 - 安装时自动创建 OpenClaw 定时任务
"""
import subprocess
import json
import os

def get_workdir():
    """获取当前工作目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_cron_exists(name):
    """检查定时任务是否已存在"""
    try:
        result = subprocess.run(
            ['openclaw', 'cron', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for job in data.get('jobs', []):
                if job.get('name') == name:
                    return True
        return False
    except Exception as e:
        print(f"⚠️  检查定时任务失败: {e}")
        return False

def create_cron_job():
    """创建定时任务"""
    workdir = get_workdir()
    job_name = "ai-news-daily-push"
    
    # 检查是否已存在
    if check_cron_exists(job_name):
        print(f"⏭️  定时任务 '{job_name}' 已存在，跳过创建")
        return
    
    # 构建命令
    cmd = [
        'openclaw', 'cron', 'add',
        '--name', job_name,
        '--schedule', '0 9 * * *',
        '--tz', 'Asia/Shanghai',
        '--session-target', 'isolated',
        '--delivery-mode', 'announce',
        '--message', f'''请执行以下步骤推送 AI 新闻日报：

1. 运行抓取脚本：
   cd {workdir} && python3 src/daily_fetch.py

2. 读取数据库获取新闻：
   python3 -c "
import sqlite3
conn = sqlite3.connect('{workdir}/data/news.db')
cursor = conn.cursor()
cursor.execute('SELECT title, source, url, raw_content FROM articles ORDER BY fetched_at DESC LIMIT 10')
rows = cursor.fetchall()
for i, row in enumerate(rows, 1):
    print(f'--- Article {{i}} ---')
    print(f'Source: {{row[1]}}')
    print(f'Title: {{row[0]}}')
    print(f'URL: {{row[2]}}')
    print(f'Content: {{row[3][:1500]}}...' if row[3] else 'Content: (empty)')
    print()
conn.close()
"

3. 基于原始内容，为每条新闻生成 200-250 字的中文摘要（英文内容翻译成中文）

4. 按以下格式推送消息：
📰 **AI 每日新闻 - [日期]**
共 10 条精选
──────────────────────────────
**1. [来源] 标题**
200-250字中文摘要...
🔗 [阅读原文](url)
...
🤖 AI News Aggregator | 每日更新'''
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ 定时任务创建成功！")
            print("📅 每天早上 9:00 自动推送 AI 新闻")
            print("")
            print("📋 任务详情:")
            print(f"   名称: {job_name}")
            print(f"   时间: 每天 9:00 AM (Asia/Shanghai)")
            print(f"   推送: 自动生成摘要并推送到当前对话")
            print("")
            print("💡 管理命令:")
            print(f"   查看: openclaw cron list")
            print(f"   删除: openclaw cron remove <job-id>")
        else:
            print(f"❌ 创建失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        print("")
        print("💡 请手动创建定时任务:")
        print("   openclaw cron add --name ai-news-daily-push --schedule '0 9 * * *' --message '...'")

def main():
    print("="*60)
    print("🤖 AI 新闻日报 v1.0.2 - 自动设置")
    print("="*60)
    print("")
    
    # 检查 openclaw 是否可用
    try:
        result = subprocess.run(['openclaw', '--version'], capture_output=True, timeout=5)
        print("✅ OpenClaw CLI 已安装")
    except FileNotFoundError:
        print("❌ OpenClaw CLI 未安装")
        print("   请先安装 OpenClaw: https://docs.openclaw.ai")
        return
    except Exception as e:
        print(f"⚠️  检查 OpenClaw 失败: {e}")
    
    print("")
    print("📅 正在创建定时任务...")
    print("")
    
    create_cron_job()
    
    print("")
    print("="*60)
    print("设置完成！")
    print("="*60)

if __name__ == "__main__":
    main()
