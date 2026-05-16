#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time
import sys
import re

def get_xiaohongshu_hot():
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
            # 尝试访问小红书首页（不需要登录也能看到部分内容）
            print('正在访问小红书...')
            page.goto('https://www.xiaohongshu.com/', timeout=60000)
            time.sleep(5)
            
            # 截图
            page.screenshot(path='/tmp/xiaohongshu_hot.png', full_page=True)
            print('已保存截图到 /tmp/xiaohongshu_hot.png')
            
            # 尝试点击"发现"或"热门"标签
            try:
                # 查找并点击发现/热门按钮
                discover_button = page.locator('text=发现').first
                if discover_button.is_visible(timeout=2000):
                    discover_button.click()
                    time.sleep(3)
            except:
                pass
            
            # 获取页面文本内容
            content = page.evaluate("""
                () => {
                    return document.body.innerText;
                }
            """)
            
            # 尝试提取笔记标题
            titles = page.evaluate("""
                () => {
                    const items = [];
                    // 尝试多种选择器
                    const selectors = [
                        '[class*="title"]',
                        '[class*="note-title"]',
                        '[class*="card-title"]',
                        'a[href*="/explore"]',
                        '[class*="content"]'
                    ];
                    
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const text = el.textContent?.trim();
                            if (text && text.length > 5 && text.length < 100) {
                                items.push(text);
                            }
                        });
                        if (items.length > 10) break;
                    }
                    
                    return [...new Set(items)]; // 去重
                }
            """)
            
            # 输出结果
            print('\n📕 小红书热门内容\n')
            
            if titles and len(titles) > 0:
                for idx, title in enumerate(titles[:30], 1):
                    # 过滤掉导航和无关内容
                    if not any(x in title for x in ['小红书', '登录', '注册', '首页', '发现', '我的', '搜索', '关注', '推荐', '穿搭', '美食']):
                        print(f"{idx}. {title}")
            else:
                print('⚠️ 小红书需要登录才能查看完整热榜内容')
                print('建议：手动在浏览器中登录小红书后再运行此脚本')
                print('\n页面内容预览：')
                # 提取可能的笔记标题
                lines = content.split('\n')
                for line in lines[:50]:
                    line = line.strip()
                    if line and len(line) > 10 and len(line) < 80:
                        if not any(x in line for x in ['小红书', '登录', '注册', 'ICP', '营业执照', '电话', '地址']):
                            print(f"• {line}")
            
        except Exception as e:
            print(f'错误: {e}', file=sys.stderr)
            return 1
        finally:
            browser.close()
    
    return 0

if __name__ == '__main__':
    sys.exit(get_xiaohongshu_hot())
