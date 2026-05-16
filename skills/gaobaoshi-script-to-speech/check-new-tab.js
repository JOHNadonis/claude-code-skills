const { connectToPage, evaluate } = require('./scripts/cdp-helper.js');

(async () => {
  console.log('等待20秒页面加载...');
  await new Promise(r => setTimeout(r, 20000));
  
  const { ws } = await connectToPage(0);

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
