#!/usr/bin/env python3
"""
推送脚本 - 将生成的消息推送到指定频道
"""
import os
import sys
import yaml

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_config():
    """加载配置"""
    config_path = 'config/config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def push_to_webchat(message_file):
    """推送到 webchat 频道
    
    由于 skill 运行在隔离环境，这里创建一个标记文件
    通知外部系统消息已准备好推送
    """
    import json
    
    # 读取消息内容
    with open(message_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建推送标记文件
    push_marker = {
        'channel': 'webchat',
        'type': 'ai_news_daily',
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'message_file': message_file,
        'content': content
    }
    
    marker_file = 'data/push_marker.json'
    with open(marker_file, 'w', encoding='utf-8') as f:
        json.dump(push_marker, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 推送标记已创建: {marker_file}")
    print(f"📄 消息已保存到: {message_file}")
    print("")
    print("💡 提示: 消息已准备好推送")
    print("   在 OpenClaw 中运行以下命令发送:")
    print(f"   message.send(file='{message_file}', channel='webchat')")
    
    return marker_file

def main():
    """主函数"""
    config = load_config()
    
    # 检查是否启用自动推送
    if not config.get('push', {}).get('openclaw', {}).get('auto_push'):
        print("⏭️  自动推送已禁用")
        return
    
    # 获取消息文件路径
    message_file = config['push']['openclaw']['output_file']
    
    if not os.path.exists(message_file):
        print(f"❌ 消息文件不存在: {message_file}")
        sys.exit(1)
    
    # 获取目标频道
    target = config['push']['openclaw'].get('target', 'webchat')
    
    if target == 'webchat':
        push_to_webchat(message_file)
    else:
        print(f"⚠️  不支持的推送目标: {target}")

if __name__ == "__main__":
    main()
