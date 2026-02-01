import argparse
import sys

from http2md.crawler import fetch_html
from markdownify import markdownify as md
import subprocess

def main()->None:
    parser = argparse.ArgumentParser(description="Convert HTTP content to Markdown")
    parser.add_argument("url", nargs="?", help="URL to process")
    parser.add_argument("--html", action="store_true", help="Output raw HTML instead of Markdown")
    parser.add_argument("--wait-until", choices=["auto", "load", "domcontentloaded", "networkidle", "commit"], default="auto", help="Wait strategy (default: auto)")
    parser.add_argument("--timeout", type=int, default=30000, help="Timeout in milliseconds (default: 30000)")
    parser.add_argument("--wait-for", type=str, default=None, help="CSS selector to wait for before extracting content")
    parser.add_argument("-o", "--out", type=str, default=None, help="Output file path")
    
    args = parser.parse_args()

    if args.url == "install":
        print("Installing Playwright browsers...")
        try:
            subprocess.check_call([sys.executable, "-m", "playwright", "install"])
            print("Successfully installed browsers.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install browsers: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    if args.url:
        try:
            html = fetch_html(args.url, wait_until=args.wait_until, timeout=args.timeout, wait_for=args.wait_for)
            if args.html:
                output = html
            else:
                output = md(html)
            
            if args.out:
                with open(args.out, "w", encoding="utf-8") as f:
                    f.write(output)
                print(f"Saved to {args.out}")
            else:
                print(output)
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                print(f"Error: Playwright browsers not found.\nPlease run:\n    http2md install", file=sys.stderr)
            else:
                print(f"Error processing {args.url}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
