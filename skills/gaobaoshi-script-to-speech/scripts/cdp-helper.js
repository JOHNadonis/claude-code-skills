/**
 * Chrome DevTools Protocol (CDP) 辅助工具
 * 用于连接已开启远程调试的 Chrome 浏览器
 */
const WebSocket = require('ws');
const http = require('http');

async function getPages() {
  return new Promise((resolve, reject) => {
    http.get('http://localhost:9222/json', (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    }).on('error', reject);
  });
}

async function sendCDP(ws, method, params = {}) {
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
}

async function connectToPage(pageIndex = 0) {
  const pages = await getPages();
  const page = pages[pageIndex];
  if (!page) throw new Error('No page found');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve) => ws.on('open', resolve));
  return { ws, page };
}

async function evaluate(ws, expression) {
  const result = await sendCDP(ws, 'Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise: true
  });
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails));
  }
  return result.result.value;
}

async function navigate(ws, url) {
  await sendCDP(ws, 'Page.navigate', { url });
  await new Promise(resolve => setTimeout(resolve, 3000));
}

async function screenshot(ws, path) {
  const { data } = await sendCDP(ws, 'Page.captureScreenshot', { format: 'png' });
  require('fs').writeFileSync(path, Buffer.from(data, 'base64'));
  return path;
}

module.exports = { getPages, sendCDP, connectToPage, evaluate, navigate, screenshot };
