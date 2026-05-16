#!/usr/bin/env node
/**
 * 大明白专业讲解系统 - 批量抓取脚本
 *
 * 用法:
 *   node scrape-damingbai.js <专业类名称> [输出目录]
 *
 * 示例:
 *   node scrape-damingbai.js 计算机类
 *   node scrape-damingbai.js 自动化类 /tmp
 *
 * 前提: Chrome 已通过 --remote-debugging-port=9222 启动
 */
const { connectToPage, navigate, evaluate } = require('./cdp-helper.js');
const fs = require('fs');
const path = require('path');

const MAJOR_NAME = process.argv[2];
const OUTPUT_DIR = process.argv[3] || '/tmp';

if (!MAJOR_NAME) {
  console.error('用法: node scrape-damingbai.js <专业类名称> [输出目录]');
  console.error('示例: node scrape-damingbai.js 计算机类');
  process.exit(1);
}

const BASE_URL = 'https://damingbai.com/major/%E5%A4%A7%E6%98%8E%E7%99%BD%E4%B8%93%E4%B8%9A%E8%AE%B2%E8%A7%A3%E7%B3%BB%E7%BB%9F.html?major=';

(async () => {
  console.log(`\n🎯 抓取: ${MAJOR_NAME}`);
  console.log(`📁 输出目录: ${OUTPUT_DIR}\n`);

  // 1. Connect
  const { ws } = await connectToPage(0);
  console.log('✅ 已连接 Chrome CDP');

  // 2. Navigate
  const url = BASE_URL + encodeURIComponent(MAJOR_NAME);
  await navigate(ws, url);
  await new Promise(r => setTimeout(r, 5000));

  const title = await evaluate(ws, 'document.title');
  console.log(`📄 页面标题: ${title}`);

  // 3. Check Reveal.js
  const totalSlides = await evaluate(ws, 'typeof Reveal !== "undefined" ? Reveal.getTotalSlides() : 0');
  if (totalSlides === 0) {
    console.error('❌ 未检测到 Reveal.js 或页面未加载完成');
    console.error('   可能原因: 需要登录、URL 错误、或页面加载慢');
    ws.close();
    process.exit(1);
  }
  console.log(`📊 总页数: ${totalSlides}\n`);

  // 4. Scrape all slides
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

    // Progress bar
    const pct = Math.round((i + 1) / totalSlides * 100);
    const bar = '█'.repeat(Math.round(pct / 5)) + '░'.repeat(20 - Math.round(pct / 5));
    process.stdout.write(`\r   ${bar} ${pct}% (${i + 1}/${totalSlides}) ${parsed.slideTitle.substring(0, 20)}`);
  }
  console.log('\n');

  // 5. Save raw JSON
  const jsonPath = path.join(OUTPUT_DIR, `damingbai-${MAJOR_NAME}-raw.json`);
  fs.writeFileSync(jsonPath, JSON.stringify(allData, null, 2), 'utf-8');

  // 6. Generate structured Markdown
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

  // 7. Summary
  const withContent = allData.filter(d => d.scriptText.length > 0);
  const totalChars = allData.reduce((s, d) => s + d.scriptText.length, 0);

  console.log('✅ 抓取完成！');
  console.log(`   📊 总页数: ${allData.length}`);
  console.log(`   📝 有文稿: ${withContent.length} 页`);
  console.log(`   📏 总字数: ${totalChars.toLocaleString()} 字`);
  console.log(`   💾 JSON:   ${jsonPath}`);
  console.log(`   💾 MD:     ${mdPath}`);

  // Show structure
  console.log('\n📋 页面结构:');
  for (const page of allData) {
    const icon = page.scriptText.length > 0 ? '📝' : '  ';
    const chars = page.scriptText.length > 0 ? `(${page.scriptText.length}字)` : '';
    console.log(`   ${icon} P${String(page.page).padStart(2)}: ${page.slideTitle.substring(0, 35)} ${chars}`);
  }

  ws.close();
})().catch(e => {
  console.error('❌ 错误:', e.message);
  process.exit(1);
});
