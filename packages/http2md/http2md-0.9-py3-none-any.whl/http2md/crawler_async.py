
import asyncio
import os
import re
import sys
from typing import Optional, Callable
from urllib.parse import urlparse, urljoin
from collections import deque

from playwright.async_api import async_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError
from markdownify import markdownify as md

# Reuse functions from existing modules where possible
from http2md.crawler_site import normalize_url, matches_patterns, url_to_filename, ProgressCallback

class AsyncCrawler:
    def __init__(self, max_concurrent: int = 5, headless: bool = True):
        self.max_concurrent = max_concurrent
        self.headless = headless
        self.browser = None
        self.context = None
        self.playwright = None
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch_page(self, url: str, wait_until: str = "auto", timeout: int = 30000, wait_for: Optional[str] = None) -> tuple[str, list[str]]:
        async with self.semaphore:
            page = await self.context.new_page()
            try:
                # Navigate
                if wait_until == "auto":
                    try:
                        await page.goto(url, wait_until="networkidle", timeout=timeout)
                    except PlaywrightTimeoutError:
                        pass # Valid fallback
                else:
                    await page.goto(url, wait_until=wait_until, timeout=timeout)
                
                if wait_for:
                    await page.wait_for_selector(wait_for, timeout=timeout)

                # Auto-scroll logic (copied from crawler.py but async)
                try:
                    await page.evaluate("""async () => {
                        await new Promise((resolve) => {
                            let totalHeight = 0;
                            const distance = 100;
                            const timer = setInterval(() => {
                                const scrollHeight = document.body.scrollHeight;
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                if(totalHeight >= scrollHeight){
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, 100);
                        });
                    }""")
                    await page.wait_for_timeout(1000)
                except Exception:
                    pass

                html = await page.content()
                
                # Extract links
                links = await page.evaluate("""() => {
                    const links = [];
                    const anchors = document.querySelectorAll('a[href]');
                    anchors.forEach(a => {
                        const href = a.href; 
                        if (href && !href.startsWith('javascript:') && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
                            links.push(href);
                        }
                    });
                    return [...new Set(links)];
                }""")
                
                return html, links
            finally:
                await page.close()

async def crawl_site_async(
    start_url: str,
    depth: int = 1,
    outdir: Optional[str] = None,
    jobs: int = 5,
    callback: Optional[ProgressCallback] = None,
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    same_domain: bool = True,
    wait_until: str = "auto",
    timeout: int = 30000,
    wait_for: Optional[str] = None,
    output_html: bool = False,
) -> list[dict]:
    
    start_url = normalize_url(start_url)
    base_parsed = urlparse(start_url)
    base_domain = base_parsed.netloc
    
    if outdir:
        os.makedirs(outdir, exist_ok=True)

    crawler = AsyncCrawler(max_concurrent=jobs)
    await crawler.start()

    # Queue items: (url, depth)
    queue = asyncio.Queue()
    queue.put_nowait((start_url, 0))
    
    visited = set()
    # We need to track what we have *queued* or *visited* to avoid duplicate processing
    # visited set will track URLs that have been finished OR are currently processing/queued
    visited.add(start_url)
    
    results = []
    
    # Statistics
    total_discovered = 1
    processed = 0

    async def worker():
        nonlocal processed, total_discovered
        while True:
            try:
                url, current_depth = await queue.get()
            except asyncio.CancelledError:
                return

            # Note: Filters are checked *before* putting into queue for child links,
            # but for the start_url we check here if we want (though logic below handles children)
            
            # Progress: fetching
            if callback:
                 # Note: callback is sync, but calling it from async is fine if it's just print
                 # If it blocked, we'd need run_in_executor
                 callback(url, "fetching", processed + 1, total_discovered, None, None)

            try:
                html, links = await crawler.fetch_page(url, wait_until, timeout, wait_for)
                
                content = html if output_html else md(html)
                filename = url_to_filename(url, start_url)
                
                if outdir:
                    filepath = os.path.join(outdir, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                
                result = {
                    "url": url,
                    "filename": filename,
                    "content": content,
                    "status": "success"
                }
                results.append(result)
                
                processed += 1
                if callback:
                    callback(url, "done", processed, total_discovered, html, content)

                # Process links
                if current_depth < depth:
                    for link in links:
                        # Normalize
                        # Link is already absolute from page.evaluate, but might have fragments
                        link = normalize_url(link)
                        
                        if link in visited:
                            continue
                        
                        # Domain check
                        if same_domain:
                            link_parsed = urlparse(link)
                            if link_parsed.netloc != base_domain:
                                continue
                                
                        # Filters
                        if include and not matches_patterns(link, include):
                            continue
                        if exclude and matches_patterns(link, exclude):
                            continue
                            
                        visited.add(link)
                        total_discovered += 1
                        queue.put_nowait((link, current_depth + 1))

            except Exception as e:
                processed += 1
                result = {
                    "url": url,
                    "filename": url_to_filename(url, start_url),
                    "content": None,
                    "status": f"error: {e}"
                }
                results.append(result)
                if callback:
                    callback(url, f"error: {e}", processed, total_discovered, None, None)
            finally:
                queue.task_done()

    # Start workers
    workers = [asyncio.create_task(worker()) for _ in range(jobs)]
    
    # Wait until queue is fully processed
    await queue.join()
    
    # Cancel workers
    for w in workers:
        w.cancel()
    
    # Wait for cancellation
    await asyncio.gather(*workers, return_exceptions=True)
    
    await crawler.close()
    return results
