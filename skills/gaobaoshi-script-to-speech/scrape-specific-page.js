#!/usr/bin/env node
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

const PAGE_ID = process.argv[2];
const MAJOR_NAME = process.argv[3];
const OUTPUT_DIR = process.argv[4] || '/tmp';

if (!PAGE_ID || !MAJOR_NAME) {
  console.error('用法: node scrape-specific-page.js <页面ID> <专业类名称> [输出目录]');
  process.exit(1);
}

const sendCDP = (ws, method, params = {}) => {
  const id = Math.floor(Math.random() * 100000);
  return new Promise((resolve, reject) => {
    const handler = (raw) => {
      const msg = JSON.parse(raw);
      if (msg.id === id) {
        ws.removeListener('message', handler);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result);
      }
    };
    ws.on('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
    setTimeout(() => { ws.removeListener('message', handler); reject(new Error('timeout')); }, 60000);
  });
};

const evaluate = async (ws, expression) => {
  const result = await sendCDP(ws, 'Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise: true
  });
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails));
  }
  return result.result.value;
};

(async () => {
  console.log(`\n🎯 抓取: ${MAJOR_NAME}`);
  console.log(`📁 输出目录: ${OUTPUT_DIR}\n`);

  const wsUrl = `ws://localhost:9222/devtools/page/${PAGE_ID}`;
  const ws = new WebSocket(wsUrl);
  await new Promise(resolve => ws.on('open', resolve));
  console.log('✅ 已连接 Chrome CDP');

  await new Promise(r => setTimeout(r, 2000));

  const title = await evaluate(ws, 'document.title');
  console.log(`📄 页面标题: ${title}`);

  const totalSlides = await evaluate(ws, 'typeof Reveal !== "undefined" ? Reveal.getTotalSlides() : 0');
  if (totalSlides === 0) {
    console.error('❌ 未检测到 Reveal.js 或页面未加载完成');
    ws.close();
    process.exit(1);
  }
  console.log(`📊 总页数: ${totalSlides}\n`);

  const allData = [];
  for (let i = 0; i < totalSlides; i++) {
    await evaluate(ws, `Reveal.slide(${i})`);
    await new Promise(r => setTimeout(r, 1500));

    const slideData = await evaluate(ws, `(() => {
      const section = document.querySelector('section.present');
      const scriptEl = document.querySelector('#script-content');
      const slideTitle = section ? (section.querySelector('.content-question, .cover-title, h1, h2, h3, .content-header') || {}).textContent || '' : '';
      const slideClass = section ? section.className : '';
      const scriptText = scriptEl ? scriptEl.innerText.trim() : '';
      const indicator = document.querySelector('.slide-indicator');
      const pageInfo = indicator ? indicator.innerText.trim() : '';
      return JSON.stringify({ slideTitle: slideTitle.trim(), slideClass, scriptText, pageInfo });
    })()`);

    const parsed = JSON.parse(slideData);
    allData.push({ page: i + 1, ...parsed });

    const pct = Math.round((i + 1) / totalSlides * 100);
    const bar = '█'.repeat(Math.round(pct / 5)) + '░'.repeat(20 - Math.round(pct / 5));
    process.stdout.write(`\r   ${bar} ${pct}% (${i + 1}/${totalSlides}) ${parsed.slideTitle.substring(0, 20)}`);
  }
  console.log('\n');

  const jsonPath = path.join(OUTPUT_DIR, `damingbai-${MAJOR_NAME}-raw.json`);
  fs.writeFileSync(jsonPath, JSON.stringify(allData, null, 2), 'utf-8');

  let md = `# ${MAJOR_NAME} · 专业讲解文稿（原始书面稿）\n\n`;
  md += `> 来源：大明白 AI 升学数据库 (damingbai.com)\n`;
  md += `> 抓取时间：${new Date().toISOString().split('T')[0]}\n`;
  md += `> 总页数：${allData.length}，含文稿页数：${allData.filter(d => d.scriptText.length > 0).length}\n\n`;
  md += '---\n\n';

  for (const page of allData) {
    if (page.slideClass.includes('cover-slide')) {
      md += `## 封面\n\n**${page.slideTitle}**\n\n`;
      if (page.scriptText) md += page.scriptText + '\n\n';
    } else if (page.slideClass.includes('toc-slide')) {
      md += `## 目录\n\n`;
      if (page.scriptText) md += page.scriptText + '\n\n';
    } else if (page.slideClass.includes('section-slide')) {
      md += `## ${page.slideTitle}\n\n`;
      if (page.scriptText) md += page.scriptText + '\n\n';
    } else if (page.slideClass.includes('content-slide')) {
      md += `### 第 ${page.page} 页：${page.slideTitle}\n\n`;
      if (page.scriptText) md += page.scriptText + '\n\n';
      else md += '*（本页无讲解文稿）*\n\n';
    } else {
      md += `### 第 ${page.page} 页${page.slideTitle ? '：' + page.slideTitle : ''}\n\n`;
      if (page.scriptText) md += page.scriptText + '\n\n';
    }
    md += '---\n\n';
  }

  const mdPath = path.join(OUTPUT_DIR, `damingbai-${MAJOR_NAME}-书面稿.md`);
  fs.writeFileSync(mdPath, md, 'utf-8');

  const withContent = allData.filter(d => d.scriptText.length > 0);
  const totalChars = allData.reduce((s, d) => s + d.scriptText.length, 0);

  console.log('✅ 抓取完成！');
  console.log(`   📊 总页数: ${allData.length}`);
  console.log(`   📝 有文稿: ${withContent.length} 页`);
  console.log(`   📏 总字数: ${totalChars.toLocaleString()} 字`);
  console.log(`   💾 JSON:   ${jsonPath}`);
  console.log(`   💾 MD:     ${mdPath}`);

  ws.close();
})();
