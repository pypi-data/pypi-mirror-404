import argparse
import sys
import subprocess

from http2md.crawler import fetch_html
from http2md.crawler_site import crawl_site
from http2md.crawler_async import crawl_site_async
from markdownify import markdownify as md
import asyncio

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
from typing import Optional

def progress_callback(url: str, status: str, current: int, total: int, html: Optional[str] = None, markdown: Optional[str] = None) -> None:
    """Default progress callback for CLI."""
    print(f"[{current}/{total}] {status}: {url}", file=sys.stderr, flush=True)


def async_main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Convert HTTP content to Markdown (Async Mode)")
    parser.add_argument("url", help="URL to crawl")
    parser.add_argument("--depth", type=int, default=1, help="Crawl depth")
    parser.add_argument("--outdir", type=str, default=".", help="Output directory")
    parser.add_argument("--jobs", "-j", type=int, default=5, help="Number of concurrent jobs")
    parser.add_argument("--include", type=str, action="append", default=[], help="Include patterns")
    parser.add_argument("--exclude", type=str, action="append", default=[], help="Exclude patterns")
    parser.add_argument("--no-same-domain", action="store_true", help="Allow following links to other domains")
    parser.add_argument("--html", action="store_true", help="Output raw HTML")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
    parser.add_argument("--tqdm", action="store_true", help="Use tqdm progress bar")
    
    args = parser.parse_args(argv)
    
    # Setup callback
    callback = progress_callback
    pbar = None
    
    if args.quiet:
        callback = None
    elif args.tqdm:
        if not TQDM_AVAILABLE:
            print("Error: tqdm not installed", file=sys.stderr)
            sys.exit(1)
        pbar = tqdm(unit="pages")
        def tqdm_callback(url: str, status: str, current: int, total: int, html: Optional[str] = None, markdown: Optional[str] = None) -> None:
            pbar.total = total
            if status == "fetching":
                pbar.set_description(f"Fetching {url[:50]}")
            elif status == "done" or status.startswith("skipped") or status.startswith("error"):
                pbar.update(1)
            pbar.refresh()
        callback = tqdm_callback

    try:
        results = asyncio.run(crawl_site_async(
            args.url,
            depth=args.depth,
            outdir=args.outdir,
            jobs=args.jobs,
            callback=callback,
            include=args.include,
            exclude=args.exclude,
            same_domain=not args.no_same_domain,
            output_html=args.html
        ))
        
        if pbar:
            pbar.close()
            
        success = sum(1 for r in results if r["status"] == "success")
        print(f"\nAsync crawled {success}/{len(results)} pages to {args.outdir}")
        
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    # Dispatch to async mode if first arg is 'async'
    if len(sys.argv) > 1 and sys.argv[1] == "async":
        async_main(sys.argv[2:])
        return

    parser = argparse.ArgumentParser(description="Convert HTTP content to Markdown")
    parser.add_argument("url", nargs="?", help="URL to process")
    
    # Output options
    parser.add_argument("--html", action="store_true", help="Output raw HTML instead of Markdown")
    parser.add_argument("-o", "--out", type=str, default=None, help="Output file path (single page)")
    parser.add_argument("--outdir", type=str, default=None, help="Output directory (for crawling)")
    
    # Wait options
    parser.add_argument("--wait-until", choices=["auto", "load", "domcontentloaded", "networkidle", "commit"], default="auto", help="Wait strategy (default: auto)")
    parser.add_argument("--timeout", type=int, default=30000, help="Timeout in milliseconds (default: 30000)")
    parser.add_argument("--wait-for", type=str, default=None, help="CSS selector to wait for before extracting content")
    
    # Crawling options
    parser.add_argument("--depth", type=int, default=None, help="Crawl depth (0=single page, 1=links from page, etc.)")
    parser.add_argument("--include", type=str, action="append", default=[], help="Include URLs matching glob pattern (can be used multiple times)")
    parser.add_argument("--exclude", type=str, action="append", default=[], help="Exclude URLs matching glob pattern (can be used multiple times)")
    parser.add_argument("--no-same-domain", action="store_true", help="Allow following links to other domains")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
    parser.add_argument("--tqdm", action="store_true", help="Use tqdm progress bar")
    
    args = parser.parse_args()

    # Handle install command
    if args.url == "install":
        print("Installing Playwright browsers...")
        try:
            subprocess.check_call([sys.executable, "-m", "playwright", "install"])
            print("Successfully installed browsers.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install browsers: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    if not args.url:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Crawling mode (depth specified or outdir specified)
        # Crawling mode (depth specified or outdir specified)
        if args.depth is not None:
            outdir = args.outdir or "."
            
            # Setup progress callback
            callback = progress_callback
            pbar = None
            
            if args.quiet:
                callback = None
            elif args.tqdm:
                if not TQDM_AVAILABLE:
                    print("Error: tqdm not installed. Please install it with: pip install tqdm", file=sys.stderr)
                    sys.exit(1)
                
                # We don't know the total size initially, so we just update usage
                pbar = tqdm(unit="pages")
                
                def tqdm_callback(url: str, status: str, current: int, total: int, html: Optional[str] = None, markdown: Optional[str] = None) -> None:
                    pbar.total = total
                    
                    if status == "fetching":
                        pbar.set_description(f"Fetching {url[:50]}")
                    elif status == "done" or status.startswith("skipped") or status.startswith("error"):
                        pbar.update(1)
                    
                    pbar.refresh()
                
                callback = tqdm_callback

            results = crawl_site(
                args.url,
                depth=args.depth,
                outdir=outdir,
                callback=callback,
                include=args.include if args.include else None,
                exclude=args.exclude if args.exclude else None,
                same_domain=not args.no_same_domain,
                wait_until=args.wait_until,
                timeout=args.timeout,
                wait_for=args.wait_for,
                output_html=args.html,
            )
            
            if pbar:
                pbar.close()

            # Summary
            success = sum(1 for r in results if r["status"] == "success")
            print(f"\nCrawled {success}/{len(results)} pages to {outdir}")
        
        # Single page mode
        else:
            html = fetch_html(
                args.url,
                wait_until=args.wait_until,
                timeout=args.timeout,
                wait_for=args.wait_for
            )
            
            if args.html:
                output = html
            else:
                output = md(html)
            
            if args.out:
                with open(args.out, "w", encoding="utf-8") as f:
                    f.write(output)
                print(f"Saved to {args.out}")
            elif args.outdir:
                import os
                os.makedirs(args.outdir, exist_ok=True)
                filepath = os.path.join(args.outdir, "index.md")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(output)
                print(f"Saved to {filepath}")
            else:
                print(output)
    
    except Exception as e:
        if "Executable doesn't exist" in str(e):
            print(f"Error: Playwright browsers not found.\nPlease run:\n    http2md install", file=sys.stderr)
        else:
            print(f"Error processing {args.url}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
