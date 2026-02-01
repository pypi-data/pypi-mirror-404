from playwright.sync_api import sync_playwright, Page
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
        
        _navigate_and_wait(page, url, wait_until, timeout, wait_for)
        
        html = page.content()
        browser.close()
        return html


def fetch_html_and_links(
    url: str,
    wait_until: str = "auto",
    timeout: int = 30000,
    wait_for: str | None = None
) -> tuple[str, list[str]]:
    """
    Fetches HTML and extracts links from the RENDERED DOM (after JavaScript execution).
    
    Returns:
        Tuple of (html_content, list_of_absolute_urls)
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        _navigate_and_wait(page, url, wait_until, timeout, wait_for)
        
        # Auto-scroll to bottom to trigger lazy loading
        try:
            page.evaluate("""async () => {
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
            # Wait a bit after scrolling for final content to settle
            page.wait_for_timeout(1000)
        except Exception:
            # Ignore scrolling errors
            pass
        
        html = page.content()
        
        # Extract links from rendered DOM using JavaScript
        links = page.evaluate("""() => {
            const links = [];
            const anchors = document.querySelectorAll('a[href]');
            anchors.forEach(a => {
                const href = a.href;  // This gives absolute URL
                if (href && !href.startsWith('javascript:') && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
                    links.push(href);
                }
            });
            return [...new Set(links)];  // Remove duplicates
        }""")
        
        browser.close()
        return html, links


def _navigate_and_wait(page: Page, url: str, wait_until: str, timeout: int, wait_for: str | None) -> None:
    """Navigate to URL and wait according to strategy."""
    if wait_until == "auto":
        try:
            page.goto(url, wait_until="networkidle", timeout=timeout)
        except PlaywrightTimeoutError:
            # If networkidle times out, we already have content loaded
            pass
    else:
        page.goto(url, wait_until=wait_until, timeout=timeout)
    
    if wait_for:
        page.wait_for_selector(wait_for, timeout=timeout)
