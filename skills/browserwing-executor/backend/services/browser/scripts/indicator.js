(scriptName, titleText, scriptLabelText, readyText) => {
    // 如果已经存在且有保护，直接返回
    if (window.__browserwingAIIndicatorProtected__) {
        return true;
    }

    // 创建或重新创建指示器的函数
    function createAIIndicator() {
        // 清理旧的闪烁定时器（如果有）
        if (window.__browserwingBlinkInterval__) {
            clearInterval(window.__browserwingBlinkInterval__);
            window.__browserwingBlinkInterval__ = null;
        }
        
        // 移除已存在的指示器（如果有）
        const existingIndicator = document.getElementById('browserwing-ai-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        // 创建容器
        const container = document.createElement('div');
        container.id = 'browserwing-ai-indicator';
        container.className = '__browserwing-protected__';
        container.style.cssText = 'position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important; pointer-events: none !important; z-index: 2147483647 !important; opacity: 1 !important; visibility: visible !important;';
        
        // 添加页面边框 - 亮蓝色主题，加粗边框，使用JS控制闪烁效果
        const border = document.createElement('div');
        border.id = 'browserwing-ai-border';
        border.className = '__browserwing-protected__';
        border.style.cssText = 'position: absolute !important; top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important; border: 8px solid #4FC3F7 !important; box-shadow: 0 0 15px #4FC3F7 !important, 0 0 30px rgba(79, 195, 247, 0.6) !important, inset 0 0 30px rgba(79, 195, 247, 0.4) !important; pointer-events: none !important; transition: opacity 0.1s ease !important;';
        
        // 添加控制面板 - 放在右边
        const panel = document.createElement('div');
        panel.id = 'browserwing-ai-panel';
        panel.className = '__browserwing-protected__';
        panel.style.cssText = 'position: absolute !important; top: 20px !important; right: 20px !important; width: 320px !important; max-width: 320px !important; min-width: 280px !important; background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%) !important; border-radius: 16px !important; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12) !important, 0 2px 8px rgba(0, 0, 0, 0.08) !important; border: 1px solid rgba(0, 0, 0, 0.08) !important; overflow: hidden !important; pointer-events: auto !important; backdrop-filter: blur(10px) !important; animation: browserwing-ai-slide-in 0.5s ease-out !important; opacity: 1 !important; visibility: visible !important; cursor: default !important; box-sizing: border-box !important;';
        
        // 头部区域（可拖动）
        const header = document.createElement('div');
        header.className = '__browserwing-protected__';
        header.style.cssText = 'padding: 20px 24px 16px !important; background: transparent !important; display: flex !important; align-items: center !important; justify-content: center !important; border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important; gap: 10px !important; opacity: 1 !important; visibility: visible !important; cursor: move !important; user-select: none !important;';
        
        // 标题
        const title = document.createElement('div');
        title.className = '__browserwing-protected__';
        title.style.cssText = 'color: #0f172a !important; font-size: 15px !important; font-weight: 600 !important; letter-spacing: -0.01em !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Helvetica, Arial, sans-serif !important; opacity: 1 !important; visibility: visible !important;';
        title.textContent = titleText;
        
        header.appendChild(title);
        
        // 脚本信息区域 - 淡红色背景
        const infoArea = document.createElement('div');
        infoArea.className = '__browserwing-protected__';
        infoArea.style.cssText = 'padding: 16px 24px !important; background: rgba(239, 68, 68, 0.03) !important; border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important; opacity: 1 !important; visibility: visible !important;';
        
        const scriptInfo = document.createElement('div');
        scriptInfo.className = '__browserwing-protected__';
        scriptInfo.style.cssText = 'display: flex !important; align-items: center !important; gap: 8px !important; color: #64748b !important; font-size: 13px !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Helvetica, Arial, sans-serif !important; opacity: 1 !important; visibility: visible !important;';
        
        const scriptLabel = document.createElement('span');
        scriptLabel.className = '__browserwing-protected__';
        scriptLabel.style.cssText = 'color: #94a3b8 !important; opacity: 1 !important; visibility: visible !important;';
        scriptLabel.textContent = scriptLabelText;
        
        const scriptNameSpan = document.createElement('span');
        scriptNameSpan.className = '__browserwing-protected__';
        scriptNameSpan.style.cssText = 'color: #475569 !important; font-weight: 500 !important; opacity: 1 !important; visibility: visible !important;';
        scriptNameSpan.textContent = scriptName || 'Untitled';
        
        scriptInfo.appendChild(scriptLabel);
        scriptInfo.appendChild(scriptNameSpan);
        infoArea.appendChild(scriptInfo);
        
        // 步骤列表显示区域
        const statusArea = document.createElement('div');
        statusArea.className = '__browserwing-protected__';
        statusArea.style.cssText = 'padding: 16px 24px 24px !important; background: transparent !important; opacity: 1 !important; visibility: visible !important; box-sizing: border-box !important; width: 100% !important; max-width: 100% !important; overflow: hidden !important;';
        
        // 步骤列表容器 - 支持滚动
        const stepsContainer = document.createElement('div');
        stepsContainer.id = 'browserwing-ai-steps-container';
        stepsContainer.className = '__browserwing-protected__';
        stepsContainer.style.cssText = 'width: 100% !important; max-width: 100% !important; max-height: 400px !important; overflow-y: auto !important; overflow-x: hidden !important; border-radius: 12px !important; background: #f8fafc !important; border: 1px solid #e2e8f0 !important; opacity: 1 !important; visibility: visible !important; box-sizing: border-box !important;';
        
        // 初始提示
        const initialHint = document.createElement('div');
        initialHint.className = '__browserwing-protected__';
        initialHint.style.cssText = 'padding: 20px !important; text-align: center !important; color: #94a3b8 !important; font-size: 13px !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Helvetica, Arial, sans-serif !important;';
        initialHint.textContent = readyText;
        
        stepsContainer.appendChild(initialHint);
        statusArea.appendChild(stepsContainer);
        
        // 组装面板
        panel.appendChild(header);
        panel.appendChild(infoArea);
        panel.appendChild(statusArea);
        
        // 添加拖动功能
        let isDragging = false;
        let currentX = 0;
        let currentY = 0;
        let initialX = 0;
        let initialY = 0;
        let xOffset = 0;
        let yOffset = 0;
        
        header.addEventListener('mousedown', function(e) {
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;
            isDragging = true;
            panel.__isDragging = false;
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', function(e) {
            if (isDragging) {
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
                xOffset = currentX;
                yOffset = currentY;
                
                if (Math.abs(currentX) > 5 || Math.abs(currentY) > 5) {
                    panel.__isDragging = true;
                }
                
                panel.style.transform = 'translate(' + currentX + 'px, ' + currentY + 'px)';
            }
        });
        
        document.addEventListener('mouseup', function() {
            if (isDragging) {
                setTimeout(function() {
                    panel.__isDragging = false;
                }, 100);
            }
            isDragging = false;
        });
        
        // 添加 CSS 动画和滚动条样式
        const style = document.createElement('style');
        style.id = 'browserwing-ai-styles';
        style.textContent = `
            @keyframes browserwing-ai-slide-in {
                from { opacity: 0 !important; transform: translateX(20px) !important; }
                to { opacity: 1 !important; transform: translateX(0) !important; }
            }
            @keyframes browserwing-ai-blink {
                0%, 100% { opacity: 1 !important; transform: scale(1) !important; }
                50% { opacity: 0.4 !important; transform: scale(0.85) !important; }
            }
            #browserwing-ai-steps-container::-webkit-scrollbar {
                width: 8px !important;
            }
            #browserwing-ai-steps-container::-webkit-scrollbar-track {
                background: #f1f5f9 !important;
                border-radius: 4px !important;
            }
            #browserwing-ai-steps-container::-webkit-scrollbar-thumb {
                background: #cbd5e1 !important;
                border-radius: 4px !important;
            }
            #browserwing-ai-steps-container::-webkit-scrollbar-thumb:hover {
                background: #94a3b8 !important;
            }
        `;
        
        // 使用 JavaScript 定时器控制边框闪烁
        let borderVisible = true;
        const blinkInterval = setInterval(() => {
            if (border && border.parentNode) {
                borderVisible = !borderVisible;
                border.style.opacity = borderVisible ? '1' : '0';
            }
        }, 750); // 每750毫秒切换一次（显示0.75秒，隐藏0.75秒）
        
        // 保存定时器以便后续清理
        window.__browserwingBlinkInterval__ = blinkInterval;
        
        // 组装容器
        container.appendChild(border);
        container.appendChild(panel);
        document.head.appendChild(style);
        
        // 确保 body 存在
        if (!document.body) {
            return null;
        }
        
        document.body.appendChild(container);
        
        return container;
    }
    
    // 创建指示器
    const container = createAIIndicator();
    
    if (!container) {
        return false;
    }
    
    // 使用 MutationObserver 保护指示器不被删除
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            // 检查是否有受保护的节点被删除
            mutation.removedNodes.forEach((node) => {
                if (node.id === 'browserwing-ai-indicator' || 
                    node.className === '__browserwing-protected__' ||
                    (node.querySelector && node.querySelector('.__browserwing-protected__'))) {
                    // 重新创建
                    setTimeout(() => {
                        if (!document.getElementById('browserwing-ai-indicator')) {
                            createAIIndicator();
                        }
                    }, 100);
                }
            });
        });
    });
    
    // 监控整个 body 的变化
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // 保存 observer 以便后续清理
    window.__browserwingAIObserver__ = observer;
    window.__browserwingAIIndicatorProtected__ = true;
    
    return true;
}