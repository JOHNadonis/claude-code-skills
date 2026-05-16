#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.request
from typing import Any

from scrapling.parser import Selector


def fetch_html(url: str, timeout: int, user_agent: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        encoding = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(encoding, errors="replace")


def run_query(selector: Selector, css: str | None, xpath: str | None, first: bool) -> Any:
    if css:
        result = selector.css(css)
        return result.get() if first else result.getall()

    if xpath:
        result = selector.xpath(xpath)
        return result.get() if first else result.getall()

    title = selector.css("title::text").get()
    headings = selector.css("h1::text, h2::text").getall()
    links = selector.css("a::attr(href)").getall()
    return {
        "title": title,
        "heading_count": len(headings),
        "headings": headings[:20],
        "link_count": len(links),
        "sample_links": links[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract data from URL using Scrapling Selector")
    parser.add_argument("url", help="Target URL")
    parser.add_argument("--css", help="CSS selector, e.g. 'h1::text'")
    parser.add_argument("--xpath", help="XPath selector, e.g. '//h1/text()'")
    parser.add_argument("--first", action="store_true", help="Return first match only")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--user-agent",
        default=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    )
    parser.add_argument("--json", action="store_true", help="Print as JSON")
    parser.add_argument("--output", help="Write output to file")

    args = parser.parse_args()

    if args.css and args.xpath:
        print("--css and --xpath are mutually exclusive", file=sys.stderr)
        return 2

    html = fetch_html(args.url, args.timeout, args.user_agent)
    selector = Selector(html)
    data = run_query(selector, args.css, args.xpath, args.first)

    if args.json or isinstance(data, (dict, list)):
        text = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        text = "" if data is None else str(data)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(text)
    else:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
