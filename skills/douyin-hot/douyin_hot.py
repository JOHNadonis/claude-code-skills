#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time
import sys

def get_douyin_hot():
    with sync_playwright() as p:
        # 使用非无头模式，模拟真实用户
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = context.new_page()
        
        try:
            page.goto('https://www.douyin.com/hot', timeout=60000)
            time.sleep(5)
            
            # 截图
            page.screenshot(path='/tmp/douyin_hot.png')
            
            # 获取页面文本内容
            content = page.evaluate("""
                () => {
                    return document.body.innerText;
                }
            """)
            
            # 解析热榜内容
            lines = content.split('\n')
            hot_list = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                # 查找热榜标题（通常在"抖音热榜"之后）
                if '抖音热榜' in line:
                    # 从下一行开始提取热榜项
                    for j in range(i+1, min(i+50, len(lines))):
                        item = lines[j].strip()
                        if item and len(item) > 5 and '万热度' in item:
                            hot_list.append(item)
                        elif item and len(item) > 5 and len(hot_list) > 0 and '万热度' not in item:
                            # 可能是标题
                            if not any(x in item for x in ['抖音', '客户端', '登录', '充钻石']):
                                hot_list.append(item)
            
            # 输出结果
            print('\n📱 抖音热榜\n')
            
            # 从内容中提取热榜
            if '抖音热榜' in content:
                idx = content.find('抖音热榜')
                hot_section = content[idx:idx+2000]
                print(hot_section)
            else:
                print('未能提取到热榜内容，请查看截图：/tmp/douyin_hot.png')
            
        except Exception as e:
            print(f'错误: {e}', file=sys.stderr)
            return 1
        finally:
            browser.close()
    
    return 0

if __name__ == '__main__':
    sys.exit(get_douyin_hot())
