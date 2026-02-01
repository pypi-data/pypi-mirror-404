"""
Site crawler module for http2md.
Crawls websites to a specified depth and converts pages to Markdown.
"""
from __future__ import annotations

import fnmatch
import os
import re
from collections import deque
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse

from markdownify import markdownify as md

from http2md.crawler import fetch_html_and_links


# Type alias for progress callback
# Type alias for progress callback: (url, status, current, total, html, markdown)
ProgressCallback = Callable[[str, str, int, int, Optional[str], Optional[str]], None]


def normalize_url(url: str) -> str:
    """Normalize URL by removing fragment and trailing slash."""
    parsed = urlparse(url)
    # Remove fragment
    normalized = parsed._replace(fragment="")
    path = normalized.path.rstrip("/") or "/"
    normalized = normalized._replace(path=path)
    return normalized.geturl()





def matches_patterns(url: str, patterns: list[str]) -> bool:
    """Check if URL matches any of the glob patterns."""
    if not patterns:
        return False
    parsed = urlparse(url)
    path = parsed.path
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(url, pattern):
            return True
    return False


def url_to_filename(url: str, base_url: str) -> str:
    """Convert URL to a safe filename."""
    parsed = urlparse(url)
    base_parsed = urlparse(base_url)
    
    # Get path relative to base
    path = parsed.path or "/"
    
    # Clean up path for filename
    if path == "/" or path == "":
        filename = "index"
    else:
        # Remove leading slash and replace slashes with underscores
        filename = path.strip("/").replace("/", "_")
    
    # Add .md extension if not present
    if not filename.endswith(".md"):
        filename += ".md"
    
    return filename


def crawl_site(
    start_url: str,
    depth: int = 1,
    outdir: Optional[str] = None,
    callback: Optional[ProgressCallback] = None,
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    same_domain: bool = True,
    wait_until: str = "auto",
    timeout: int = 30000,
    wait_for: Optional[str] = None,
    output_html: bool = False,
) -> list[dict]:
    """
    Crawl a website to a specified depth.
    
    Args:
        start_url: Starting URL to crawl.
        depth: How deep to follow links (0 = single page, 1 = links from page, etc.)
        outdir: Directory to save files. If None, returns content without saving.
        callback: Progress callback function(url, status, current, total).
        include: List of glob patterns to include.
        exclude: List of glob patterns to exclude.
        same_domain: Only follow links to the same domain.
        wait_until: Wait strategy for page loading.
        timeout: Timeout in milliseconds.
        wait_for: CSS selector to wait for.
        output_html: If True, save HTML instead of Markdown.
    
    Returns:
        List of dicts with keys: url, filename, content, status
    """
    start_url = normalize_url(start_url)
    base_parsed = urlparse(start_url)
    base_domain = base_parsed.netloc
    
    # BFS queue: (url, current_depth)
    queue: deque[tuple[str, int]] = deque([(start_url, 0)])
    visited: set[str] = set()
    results: list[dict] = []
    
    # Create output directory if specified
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    
    # For progress tracking
    total_discovered = 1
    processed = 0
    
    while queue:
        url, current_depth = queue.popleft()
        
        # Skip if already visited
        if url in visited:
            continue
        
        visited.add(url)
        processed += 1
        
        # Check filters
        if include and not matches_patterns(url, include):
            if callback:
                callback(url, "skipped (not in include)", processed, total_discovered, None, None)
            continue
        
        if exclude and matches_patterns(url, exclude):
            if callback:
                callback(url, "skipped (excluded)", processed, total_discovered, None, None)
            continue
        
        # Notify progress
        if callback:
            callback(url, "fetching", processed, total_discovered, None, None)
        
        try:
            html, links = fetch_html_and_links(
                url,
                wait_until=wait_until,
                timeout=timeout,
                wait_for=wait_for
            )
            
            # Convert to markdown if needed
            if output_html:
                content = html
            else:
                content = md(html)
            
            # Generate filename
            filename = url_to_filename(url, start_url)
            
            # Save to file if outdir specified
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
            
            if callback:
                callback(url, "done", processed, total_discovered, html, content)
            
            # Extract and queue links if not at max depth
            if current_depth < depth:
                # links are already extracted by fetch_html_and_links
                for link in links:
                    if link in visited:
                        continue
                    
                    # Check same domain
                    if same_domain:
                        link_parsed = urlparse(link)
                        if link_parsed.netloc != base_domain:
                            continue
                    
                    queue.append((link, current_depth + 1))
                    total_discovered += 1
        
        except Exception as e:
            result = {
                "url": url,
                "filename": url_to_filename(url, start_url),
                "content": None,
                "status": f"error: {e}"
            }
            results.append(result)
            
            if callback:
                callback(url, f"error: {e}", processed, total_discovered, None, None)
    
    return results
