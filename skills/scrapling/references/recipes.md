# Scrapling Recipes

## 1) HTTP Fetcher（静态页面）

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get("https://example.com")
items = page.css(".item")
print([i.css(".title::text").get() for i in items])
```

## 2) StealthyFetcher（反爬/Cloudflare 场景）

```python
from scrapling.fetchers import StealthyFetcher

StealthyFetcher.adaptive = True
page = StealthyFetcher.fetch(
    "https://target.site",
    headless=True,
    network_idle=True,
)
print(page.css("h1::text").get())
```

## 3) DynamicFetcher（JS 渲染页面）

```python
from scrapling.fetchers import DynamicFetcher

page = DynamicFetcher.fetch("https://target.site")
print(page.xpath("//title/text()").get())
```

## 4) Spider（并发爬虫）

```python
from scrapling.spiders import Spider, Response

class DemoSpider(Spider):
    name = "demo"
    start_urls = ["https://example.com"]
    concurrent_requests = 10

    async def parse(self, response: Response):
        for item in response.css(".product"):
            yield {
                "title": item.css("h2::text").get(),
                "price": item.css(".price::text").get(),
            }

result = DemoSpider().start()
result.items.to_json("items.json")
```

## 5) CLI 快速提取

```bash
scrapling extract get 'https://example.com' content.md
scrapling extract get 'https://example.com' content.txt --css-selector 'h1'
```

## 6) 常见排障

- 报错 `No module named scrapling`：先执行 `scripts/install_scrapling.sh all`
- fetchers 场景失败：补执行 `scrapling install`
- 动态页面抓不到：优先加 `network_idle=True`，必要时改 `StealthyFetcher`
