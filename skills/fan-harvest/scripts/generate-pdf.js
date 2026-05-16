#!/usr/bin/env node

/**
 * PDF Generator for Fan Harvest Skill
 * 使用 Puppeteer 将 HTML 转换为精美的 PDF 文档
 *
 * 用法: node generate-pdf.js <input.html> <output.pdf>
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function generatePDF(inputPath, outputPath) {
  // 检查输入文件
  if (!fs.existsSync(inputPath)) {
    console.error(`❌ 输入文件不存在: ${inputPath}`);
    process.exit(1);
  }

  console.log('📄 正在启动浏览器...');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();

    // 读取 HTML 内容
    const htmlContent = fs.readFileSync(inputPath, 'utf-8');

    // 设置页面内容
    await page.setContent(htmlContent, {
      waitUntil: ['networkidle0', 'domcontentloaded']
    });

    // 等待 Mermaid 图表渲染完成
    console.log('⏳ 等待图表渲染...');
    await page.waitForTimeout(2000);

    // 确保 Mermaid 图表已渲染
    await page.evaluate(() => {
      return new Promise((resolve) => {
        if (typeof mermaid !== 'undefined') {
          mermaid.run().then(resolve).catch(resolve);
        } else {
          resolve();
        }
      });
    });

    // 再等待一下确保渲染完成
    await page.waitForTimeout(1000);

    console.log('📝 正在生成 PDF...');

    // 生成 PDF
    await page.pdf({
      path: outputPath,
      format: 'A4',
      printBackground: true,
      margin: {
        top: '0',
        right: '0',
        bottom: '0',
        left: '0'
      },
      displayHeaderFooter: false,
      preferCSSPageSize: true
    });

    console.log(`✅ PDF 已生成: ${outputPath}`);

    // 获取文件大小
    const stats = fs.statSync(outputPath);
    const fileSizeKB = (stats.size / 1024).toFixed(1);
    console.log(`📊 文件大小: ${fileSizeKB} KB`);

  } catch (error) {
    console.error('❌ 生成 PDF 时出错:', error.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// 命令行参数处理
const args = process.argv.slice(2);

if (args.length < 2) {
  console.log(`
📘 粉丝变现 PDF 生成器

用法:
  node generate-pdf.js <input.html> <output.pdf>

示例:
  node generate-pdf.js ./自媒体破局路径图.html ./自媒体破局路径图.pdf

选项:
  --help    显示帮助信息
  `);
  process.exit(0);
}

const [inputPath, outputPath] = args;

// 确保输出目录存在
const outputDir = path.dirname(outputPath);
if (outputDir && !fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

generatePDF(inputPath, outputPath);
