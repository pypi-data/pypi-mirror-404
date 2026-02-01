from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError

def fetch_html(url: str, wait_until: str = "auto", timeout: int = 30000, wait_for: str | None = None) -> str:
    """
    Fetches the raw HTML content of a URL using Playwright.
    
    Args:
        url: The URL to fetch.
        wait_until: Wait strategy. Options:
            - 'auto': Combined strategy (networkidle with fallback) - DEFAULT
            - 'load', 'domcontentloaded', 'networkidle', 'commit': Playwright built-in
        timeout: Maximum time to wait in milliseconds (default 30s).
        wait_for: Optional CSS selector to wait for before extracting content.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        if wait_until == "auto":
            # Combined strategy: try networkidle, fallback to load on timeout
            try:
                page.goto(url, wait_until="networkidle", timeout=timeout)
            except PlaywrightTimeoutError:
                # If networkidle times out (page keeps making requests),
                # we already have content loaded, just continue
                pass
        else:
            page.goto(url, wait_until=wait_until, timeout=timeout)
        
        # Wait for specific selector if provided
        if wait_for:
            page.wait_for_selector(wait_for, timeout=timeout)
        
        html = page.content()
        browser.close()
        return html
