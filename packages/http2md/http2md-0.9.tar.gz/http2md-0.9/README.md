# http2md

A CLI tool to fetch web pages and convert them to Markdown using Playwright.


## Installation
```bash
pip install http2md
http2md install
```

### Docker

You can use `http2md` via Docker without installing Python or system dependencies.

1.  **Build the image** (first time only):
    ```bash
    docker-compose build
    ```

2.  **Run the crawler**:
    ```bash
    # Crawl and save to ./out_docker/
    docker-compose run --rm http2md https://example.com --outdir out
    ```

    *   The `./out_docker` directory on your host is mounted to `/app/out` inside the container.
    *   Command arguments (`--depth`, `--tqdm`, etc.) are passed directly to `http2md`.

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

# SYNC Crawl site to depth 2, save to ./docs/
http2md https://react.dev  --depth 2 --outdir ./docs

# ASYNC Increase concurrency to 10
http2md async https://react.dev --jobs 10 --outdir ./docs


```

## CLI Options

```
usage: http2md [-h] [--html]
               [--wait-until {auto,load,domcontentloaded,networkidle,commit}]
               [--timeout TIMEOUT] [--wait-for WAIT_FOR] [-o OUT]
               [url]

Convert HTTP content to Markdown. Supports:
- Headings, lists, code blocks, tables
- Links (static and dynamic)
- Images (with alt text)
- Formatting (bold, italic, **strikethrough**)

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

## Python API

You can also use `http2md` directly from Python:

```python
from http2md.crawler import fetch_html
from markdownify import markdownify as md

# Fetch raw HTML
html = fetch_html("https://example.com")

# Convert to Markdown
markdown = md(html)
print(markdown)

# With options
html = fetch_html(
    "https://spa-site.com",
    wait_until="networkidle",  # or "auto", "load", "domcontentloaded"
    timeout=60000,             # 60 seconds
    wait_for=".content"        # CSS selector to wait for
)
```

## Site Crawling

Crawl entire websites to a specified depth:

```bash
# Crawl site to depth 2, save to ./docs/
http2md https://react.dev  --depth 2 --outdir ./docs

# Only crawl /api/* pages
http2md https://react.dev  --depth 3 --include "/api/*"

# Exclude images and static files
http2md https://react.dev  --depth 2 --exclude "*.png" --exclude "*.css"

# Quiet mode (no progress output)
http2md https://react.dev  --depth 1 --outdir ./out -q
```

### Parallel Crawling (Fast Mode)

Use the `async` command to enable parallel downloading (up to 5-10x faster):

```bash
# Run with 5 concurrent jobs (default)
http2md async https://react.dev  --depth 2 --outdir ./docs

# Increase concurrency to 10
http2md async https://react.dev --jobs 10 --outdir ./docs
```

*   **Note**: This mode uses `asyncio` and reuses the browser instance, making it much faster but potentially less stable on extremely complex sites.
*   **Standard mode** (`http2md <url>`) remains synchronous and uses a fresh browser for every page (slower but maximum isolation/reliability).

### Why use Async Mode?

The async implementation (`crawler_async.py`) is designed for performance:

1.  **Architecture**: Uses `asyncio` and `playwright.async_api`.
2.  **Resource Efficiency**: Reuses a single `BrowserContext` across multiple pages instead of launching a new browser for every URL.
3.  **Concurrency**: Uses a worker pool to fetch multiple pages in parallel (controlled by `--jobs`).
4.  **Speed**: Can be 5-10x faster than the synchronous mode, especially on larger sites.

### Crawling Options

| Option | Description |
|--------|-------------|
| `--depth N` | Crawl depth (0=single page, 1=links from page, etc.) |
| `--outdir DIR` | Output directory for crawled pages |
| `--include PATTERN` | Include URLs matching glob pattern (repeatable) |
| `--exclude PATTERN` | Exclude URLs matching glob pattern (repeatable) |
| `--no-same-domain` | Allow following links to other domains |
| `--tqdm` | Use tqdm progress bar |
| `-q, --quiet` | Suppress progress output |


### Advanced Link Extraction

`http2md` automatically handles Single Page Applications (SPAs) and dynamic content:

1.  **JavaScript Execution**: It executes JavaScript to render the page fully.
2.  **Auto-Scrolling**: It automatically attempts to scroll to the bottom of the page to trigger lazy-loading of content.
3.  **Dynamic Links**: It extracts links from the *rendered* DOM (using `page.evaluate`), not just the static HTML. This ensures links generated by JavaScript are found.

Note: Sites using non-standard navigation (e.g., `onclick` on `div` elements instead of `<a>` tags) may still have limited crawlability.
### Python API for Crawling

```python
from http2md.crawler_site import crawl_site

def on_progress(url, status, current, total, html=None, markdown=None):
    print(f"[{current}/{total}] {status}: {url}")
    if html:
        print(f"  Downloaded {len(html)} bytes")

results = crawl_site(
    "https://react.dev",
    depth=2,
    outdir="./output",
    callback=on_progress,
    include=["*/api/*"],
    exclude=["*.png"]
)
```

### Using tqdm for Progress

```python
from http2md.crawler_site import crawl_site
from tqdm import tqdm

pbar = tqdm(unit="pages")

def tqdm_callback(url, status, current, total, html=None, markdown=None):
    pbar.total = total
    if status == "fetching":
        pbar.set_description(f"Fetching {url[:50]}")
    elif status == "done" or status.startswith("skipped"):
        pbar.update(1)
    pbar.refresh()

crawl_site(
    "https://docs.example.com",
    depth=2,
    callback=tqdm_callback
)
pbar.close()
)
pbar.close()
```

### Python API (Async)

For maximum performance in your own scripts, use `crawl_site_async`:

```python
import asyncio
from http2md.crawler_async import crawl_site_async

async def main():
    results = await crawl_site_async(
        "https://react.dev",
        depth=2,
        jobs=10,  # 10 concurrent requests
        outdir="./output_async"
    )
    print(f"Crawled {len(results)} pages")

if __name__ == "__main__":
    asyncio.run(main())
```

