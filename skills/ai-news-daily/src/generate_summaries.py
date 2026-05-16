#!/usr/bin/env python3
"""
AI 摘要生成模块 - v1.0.2
读取原始内容，输出 200-250 字中文摘要
"""
import json
import os
import re
import sqlite3
from datetime import datetime, timedelta

def clean_text(text):
    """清理文本"""
    if not text:
        return ""
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_core_content(text, min_chars=200, max_chars=250):
    """提取核心内容，确保200-250字"""
    if not text:
        return ""
    
    text = clean_text(text)
    
    # 如果内容本身就合适，直接返回
    if min_chars <= len(text) <= max_chars:
        return text
    
    # 如果内容太长，提取核心部分
    if len(text) > max_chars:
        # 按句子分割
        sentences = re.split(r'([。！？.!?])', text)
        result = []
        length = 0
        
        for i in range(0, len(sentences)-1, 2):
            sent = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
            if length + len(sent) > max_chars:
                # 如果还没达到最小长度，截断当前句子
                if length < min_chars:
                    remaining = max_chars - length
                    result.append(sent[:remaining])
                break
            result.append(sent)
            length += len(sent)
        
        return ''.join(result)
    
    # 如果内容太短，保留原文
    return text

def generate_article_summary(index, source, title, url, raw_content):
    """为单篇文章生成摘要（200-250字）"""
    
    # 根据来源和标题，从原始内容中提取关键信息
    content = clean_text(raw_content)
    
    # 提取核心内容
    summary = extract_core_content(content, 200, 250)
    
    # 如果提取的内容太短，补充标题信息
    if len(summary) < 200:
        summary = f"{title}。{summary}"
    
    # 如果还是太短，标记出来
    if len(summary) < 200:
        summary = summary + "（原文内容较短）"
    
    return summary

def main():
    """主函数"""
    db_path = 'data/news.db'
    output_file = 'data/openclaw_message.txt'
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取最新10条新闻
    cursor.execute('''
        SELECT title, source, url, raw_content 
        FROM articles 
        ORDER BY fetched_at DESC 
        LIMIT 10
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("❌ 没有找到新闻")
        return
    
    # 生成日期
    date_str = (datetime.now() - timedelta(days=1)).strftime('%Y年%m月%d日')
    
    # 构建输出
    lines = [
        f"📰 **AI 每日新闻 - {date_str}**",
        "",
        f"共 {len(rows)} 条精选",
        "──────────────────────────────",
        ""
    ]
    
    for i, (title, source, url, raw_content) in enumerate(rows, 1):
        lines.append(f"**{i}. [{source}] {title}**")
        lines.append("")
        
        # 生成摘要
        summary = generate_article_summary(i, source, title, url, raw_content)
        
        lines.append(summary)
        lines.append(f"🔗 [阅读原文]({url})")
        lines.append("")
    
    lines.append("──────────────────────────────")
    lines.append("🤖 AI News Aggregator | 每日更新")
    
    # 保存
    message = '\n'.join(lines)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(message)
    
    print(f"✅ 消息已生成: {output_file}")
    print(f"📊 总字数: {len(message)}")
    
    # 检查每条摘要长度
    print("\n📋 摘要长度检查:")
    for i, (title, source, url, raw_content) in enumerate(rows, 1):
        summary = generate_article_summary(i, source, title, url, raw_content)
        print(f"  {i}. {len(summary)}字 - {title[:30]}...")

if __name__ == "__main__":
    main()
