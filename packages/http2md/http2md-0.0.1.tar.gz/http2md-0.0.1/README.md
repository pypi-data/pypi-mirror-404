# http2md

A CLI tool to fetch web pages and convert them to Markdown using Playwright.

## Installation

```bash
pip install http2md
http2md install
```

## Usage

```bash
# Basic usage (converts to Markdown)
http2md https://example.com

# Basic usage out to file (converts to Markdown)
http2md https://example.com -o output.md

# Output raw HTML
http2md https://example.com --html

# Wait for a specific element before extracting
http2md https://spa-site.com --wait-for ".content"

# Increase timeout for slow sites (default: 30000ms)
http2md https://slow-site.com --timeout 60000

# Use specific wait strategy
http2md https://fast-site.com --wait-until load
```

## CLI Options

```
usage: http2md [-h] [--html]
               [--wait-until {auto,load,domcontentloaded,networkidle,commit}]
               [--timeout TIMEOUT] [--wait-for WAIT_FOR] [-o OUT]
               [url]

Convert HTTP content to Markdown

positional arguments:
  url                   URL to process

options:
  -h, --help            show this help message and exit
  --html                Output raw HTML instead of Markdown
  --wait-until          Wait strategy (default: auto)
  --timeout TIMEOUT     Timeout in milliseconds (default: 30000)
  --wait-for WAIT_FOR   CSS selector to wait for before extracting content
  -o, --out OUT         Output file path
```

### Wait Strategies

| Strategy | Description |
|----------|-------------|
| `auto` | Combined: tries `networkidle`, falls back on timeout (default) |
| `load` | Wait for `load` event |
| `domcontentloaded` | Wait for DOM to be ready |
| `networkidle` | Wait for no network activity (500ms) |
| `commit` | Return immediately after response headers |
