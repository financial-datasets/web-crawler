from urllib.parse import urljoin
import time

# Optional: Playwright for JS-rendered pages
try:
    from playwright.sync_api import sync_playwright
except ImportError:  # Playwright not installed
    sync_playwright = None

class BasePageParser:
    def __init__(self):
        self.visited_links = set()


    def get_content(self, url) -> dict:
        """
        Returns the text content from the given URL
        """
        content_data = self._get_content_with_playwright(url)
        
        output = {
            "url": url,
            "title": content_data["title"],
            "content": content_data["content"],
            "content_length": len(content_data["content"])
        }
        
        return output

    def get_links(self, url) -> dict:
        """
        Returns all links found on the page
        """
        return {
            "url": url,
            "internal_links": self._get_links_with_playwright(url),
        }

    def _get_content_with_playwright(self, url):
        """Extract readable article text using robust, generic Playwright strategy.
        Steps:
        - Load with domcontentloaded and a short wait
        - Dismiss consent/continue overlays if present
        - Auto-scroll to load lazy content
        - Use Mozilla Readability in-page to extract main article text
        - Fallback to semantic selectors, then body inner_text
        """
        if sync_playwright is None:
            raise RuntimeError("Playwright is not installed. Install with 'pip install playwright' or add to pyproject and sync.")

        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(1.5)

            # Try to click common consent/continue buttons if visible
            for selector in [
                "button:has-text('Continue')",
                "button:has-text('Continue reading')",
                "button:has-text('I agree')",
                "button:has-text('Accept')",
                "text=Continue reading",
            ]:
                try:
                    el = page.query_selector(selector)
                    if el:
                        el.click(timeout=1000)
                        time.sleep(0.5)
                except Exception:
                    pass

            # Auto-scroll to load lazy content
            try:
                page.evaluate("""
                    async () => {
                        await new Promise((resolve) => {
                            let total = 0; const step = Math.max(200, Math.floor(window.innerHeight * 0.75));
                            const timer = setInterval(() => {
                                window.scrollBy(0, step);
                                total += step;
                                if (total >= document.body.scrollHeight - window.innerHeight) {
                                    clearInterval(timer); resolve();
                                }
                            }, 150);
                        });
                    }
                """)
            except Exception:
                pass

            # Give dynamic content a moment to render
            time.sleep(1.5)

            title = page.title()

            # Inject Mozilla Readability and extract main article if possible
            article_text = None
            try:
                readability_js = """
                (() => {
                  function loadReadability(cb){
                    if (window.__readabilityLoaded) return cb();
                    const s=document.createElement('script');
                    s.src='https://cdn.jsdelivr.net/npm/@mozilla/readability@0.5.0/Readability.js';
                    s.onload=()=>{window.__readabilityLoaded=true; cb();};
                    document.head.appendChild(s);
                  }
                  return new Promise((resolve)=>{
                    loadReadability(()=>{
                      try {
                        const doc = document.cloneNode(true);
                        const article = new window.Readability(doc).parse();
                        resolve(article && article.textContent ? article.textContent : "");
                      } catch(e){ resolve(""); }
                    });
                  });
                })()
                """
                article_text = page.evaluate(readability_js)
            except Exception:
                article_text = None

            content = None
            if article_text and isinstance(article_text, str) and article_text.strip():
                content = article_text
            else:
                # Fallback selectors
                for sel in [
                    "article",
                    "main",
                    "[role='main']",
                    "div[itemprop='articleBody']",
                    "#main-content",
                    "#content",
                    "body"
                ]:
                    try:
                        content = page.inner_text(sel)
                        if content and content.strip():
                            break
                    except Exception:
                        continue

            browser.close()

        content = ' '.join((content or '').split())
        title = (title or '').strip()
        return {"title": title, "content": content}

    def _get_links_with_playwright(self, url):
        """Render a page with JavaScript and return all absolute href links.

        """
        if sync_playwright is None:
            raise RuntimeError("Playwright is not installed. Install with 'pip install playwright' or add to pyproject and sync.")

        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait 5 seconds for dynamic content to load instead of waiting for networkidle
            time.sleep(5)

            hrefs = page.eval_on_selector_all(
                "a[href]",
                "els => els.map(a => a.getAttribute('href'))",
            )

            browser.close()

        normalized = []
        for href in hrefs:
            if not href:
                continue
            h = href.strip()
            if h.startswith("javascript:") or h.startswith("mailto:") or h.startswith("#"):
                continue
            normalized.append(urljoin(url, h))

        return sorted(set(normalized))

if __name__ == "__main__":
    url = "https://www.cnbc.com/2025/07/31/apple-aapl-q3-earnings-report-2025.html"
    parser = BasePageParser()
    
    print("=== Testing Link Extraction ===")
    try:
        links = parser.get_links(url)
        print(f"Found {len(links['internal_links'])} links")
        print(f"First 5 links: {links['internal_links'][:5]}")
    except Exception as e:
        print(f"Link extraction failed: {e}")
    
    print("\n=== Testing Content Extraction ===")
    try:
        content = parser.get_content(url)
        print(f"Title: {content['title']}")
        print(f"Content length: {content['content_length']} characters")
        print(f"First 300 characters: {content['content'][:300]}...")
    except Exception as e:
        print(f"Content extraction failed: {e}")
