#!/usr/bin/env node
/**
 * Leading Indicator Monitor - PDF Report Generator
 *
 * Converts Markdown reports to beautifully styled PDF documents
 * Uses Puppeteer for high-quality PDF rendering
 *
 * Usage: node generate-pdf.mjs <input.md> [output.pdf]
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, basename, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Check if puppeteer is available
let puppeteer;
try {
  puppeteer = await import('puppeteer');
} catch (e) {
  console.error('Puppeteer not found. Installing...');
  const { execSync } = await import('child_process');
  execSync('npm install puppeteer', { stdio: 'inherit', cwd: __dirname });
  puppeteer = await import('puppeteer');
}

// Check if marked is available for Markdown parsing
let marked;
try {
  marked = await import('marked');
} catch (e) {
  console.error('Marked not found. Installing...');
  const { execSync } = await import('child_process');
  execSync('npm install marked', { stdio: 'inherit', cwd: __dirname });
  marked = await import('marked');
}

// Professional report styling
const CSS_STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {
    --primary: #2563eb;
    --primary-light: #3b82f6;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --neutral: #6b7280;
    --bg: #ffffff;
    --text: #1f2937;
    --text-secondary: #6b7280;
    --border: #e5e7eb;
    --code-bg: #f3f4f6;
  }

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: var(--text);
    background: var(--bg);
    padding: 40px 50px;
  }

  /* Header styling */
  h1 {
    font-size: 24pt;
    font-weight: 700;
    color: var(--primary);
    margin-bottom: 8px;
    padding-bottom: 12px;
    border-bottom: 3px solid var(--primary);
  }

  h2 {
    font-size: 16pt;
    font-weight: 600;
    color: var(--text);
    margin-top: 24px;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }

  h3 {
    font-size: 13pt;
    font-weight: 600;
    color: var(--text);
    margin-top: 18px;
    margin-bottom: 8px;
  }

  h4 {
    font-size: 11pt;
    font-weight: 600;
    color: var(--text-secondary);
    margin-top: 14px;
    margin-bottom: 6px;
  }

  /* Paragraph and text */
  p {
    margin-bottom: 10px;
  }

  strong {
    font-weight: 600;
    color: var(--text);
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 10pt;
  }

  th {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
    color: white;
    font-weight: 600;
    text-align: left;
    padding: 10px 12px;
  }

  td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
  }

  tr:nth-child(even) {
    background: #f9fafb;
  }

  tr:hover {
    background: #f3f4f6;
  }

  /* Code blocks */
  pre {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 16px;
    overflow-x: auto;
    margin: 12px 0;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 9pt;
    line-height: 1.5;
  }

  code {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 9pt;
    background: var(--code-bg);
    padding: 2px 6px;
    border-radius: 4px;
  }

  pre code {
    background: none;
    padding: 0;
  }

  /* Lists */
  ul, ol {
    margin: 10px 0;
    padding-left: 24px;
  }

  li {
    margin-bottom: 4px;
  }

  /* Blockquotes for insights */
  blockquote {
    border-left: 4px solid var(--primary);
    background: linear-gradient(90deg, #eff6ff 0%, transparent 100%);
    padding: 12px 16px;
    margin: 16px 0;
    border-radius: 0 6px 6px 0;
  }

  blockquote p {
    margin: 0;
    color: var(--text);
  }

  /* Signal indicators */
  .signal-green { color: var(--success); font-weight: 600; }
  .signal-yellow { color: var(--warning); font-weight: 600; }
  .signal-red { color: var(--danger); font-weight: 600; }
  .signal-gray { color: var(--neutral); font-weight: 600; }

  /* Links */
  a {
    color: var(--primary);
    text-decoration: none;
  }

  a:hover {
    text-decoration: underline;
  }

  /* Horizontal rules */
  hr {
    border: none;
    border-top: 2px solid var(--border);
    margin: 24px 0;
  }

  /* Page break hints */
  h2 {
    page-break-after: avoid;
  }

  table, pre {
    page-break-inside: avoid;
  }

  /* Footer styling */
  .report-footer {
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    font-size: 9pt;
    color: var(--text-secondary);
    text-align: center;
  }

  /* Metadata block */
  .metadata {
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
  }

  .metadata p {
    margin: 4px 0;
    font-size: 10pt;
  }

  /* Emoji support */
  .emoji {
    font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif;
  }
`;

// Convert Markdown to HTML
function markdownToHtml(markdown) {
  // Configure marked for better table support
  marked.marked.setOptions({
    gfm: true,
    breaks: true,
    tables: true,
  });

  let html = marked.marked(markdown);

  // Replace emoji indicators with styled versions
  html = html.replace(/🟢/g, '<span class="signal-green">●</span>');
  html = html.replace(/🟡/g, '<span class="signal-yellow">●</span>');
  html = html.replace(/🔴/g, '<span class="signal-red">●</span>');
  html = html.replace(/⚪/g, '<span class="signal-gray">○</span>');

  return html;
}

// Generate full HTML document
function generateHtmlDocument(markdown, ticker) {
  const content = markdownToHtml(markdown);
  const timestamp = new Date().toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });

  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>领先指标监控报告 - ${ticker}</title>
  <style>${CSS_STYLES}</style>
</head>
<body>
  ${content}

  <div class="report-footer">
    <p>本报告由 Leading Indicator Monitor Skill 自动生成</p>
    <p>生成时间: ${timestamp} | 仅供研究参考，不构成投资建议</p>
  </div>
</body>
</html>
`;
}

// Main function
async function main() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error('Usage: node generate-pdf.mjs <input.md> [output.pdf]');
    process.exit(1);
  }

  const inputFile = args[0];
  const outputFile = args[1] || inputFile.replace(/\.md$/, '.pdf');

  // Read markdown content
  if (!existsSync(inputFile)) {
    console.error(`Error: Input file not found: ${inputFile}`);
    process.exit(1);
  }

  const markdown = readFileSync(inputFile, 'utf-8');

  // Extract ticker from filename or content
  const tickerMatch = basename(inputFile).match(/^([A-Z]+)/i) ||
                      markdown.match(/股票代码[：:]\s*([A-Z]+)/i);
  const ticker = tickerMatch ? tickerMatch[1].toUpperCase() : 'REPORT';

  // Generate HTML
  const html = generateHtmlDocument(markdown, ticker);

  // Save HTML for debugging (optional)
  const htmlFile = inputFile.replace(/\.md$/, '.html');
  writeFileSync(htmlFile, html);
  console.log(`HTML saved: ${htmlFile}`);

  // Generate PDF using Puppeteer
  console.log('Launching browser for PDF generation...');
  const browser = await puppeteer.default.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'networkidle0' });

  await page.pdf({
    path: outputFile,
    format: 'A4',
    margin: {
      top: '20mm',
      right: '15mm',
      bottom: '20mm',
      left: '15mm'
    },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: `
      <div style="font-size: 9px; color: #666; width: 100%; text-align: center; padding: 5px 0;">
        领先指标监控报告 - ${ticker}
      </div>
    `,
    footerTemplate: `
      <div style="font-size: 9px; color: #666; width: 100%; text-align: center; padding: 5px 0;">
        <span class="pageNumber"></span> / <span class="totalPages"></span>
      </div>
    `
  });

  await browser.close();

  console.log(`✅ PDF generated successfully: ${outputFile}`);
  return outputFile;
}

main().catch(console.error);
