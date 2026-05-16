const WebSocket = require('ws');
const { evaluate } = require('./scripts/cdp-helper.js');

(async () => {
  const wsUrl = 'ws://localhost:9222/devtools/page/1C02F4AD2D6A398F482B6C908C31CE95';
  
  console.log('连接到机械类标签页...');
  const ws = new WebSocket(wsUrl);
  await new Promise(resolve => ws.on('open', resolve));
  
  console.log('等待10秒页面加载...');
  await new Promise(r => setTimeout(r, 10000));

  const title = await evaluate(ws, 'document.title');
  const url = await evaluate(ws, 'window.location.href');
  const hasReveal = await evaluate(ws, 'typeof Reveal !== "undefined"');
  const bodyLength = await evaluate(ws, 'document.body ? document.body.innerText.length : 0');
  const bodyPreview = await evaluate(ws, 'document.body ? document.body.innerText.substring(0, 300) : ""');
  
  console.log('\n页面标题:', title);
  console.log('URL:', url);
  console.log('Reveal.js:', hasReveal);
  console.log('内容长度:', bodyLength);
  console.log('内容预览:', bodyPreview);

  if (hasReveal) {
    const totalSlides = await evaluate(ws, 'Reveal.getTotalSlides()');
    console.log('总页数:', totalSlides);
  }

  ws.close();
})();
