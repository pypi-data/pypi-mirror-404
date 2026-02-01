"""Stealth browser crawler using Playwright."""

import asyncio
import random
import time
from urllib.parse import urljoin, urlparse
from typing import Optional

from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

from saa.config import Config
from saa.models import PageData, ImageData, LinkData, MetaTag, OpenGraphData


class Crawler:
    """Async context manager for stealth web crawling."""

    def __init__(self, config: Config, verbose: bool = False, progress_callback=None):
        self.config = config
        self.verbose = verbose
        self.progress_callback = progress_callback  # Called with (current, total, url)
        self.stealth = Stealth()
        self._playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None

    async def __aenter__(self):
        """Start browser with stealth."""
        self._playwright = await async_playwright().start()

        # Only pass executable_path if explicitly configured
        launch_opts = {"headless": self.config.headless}
        if self.config.chromium_path:
            launch_opts["executable_path"] = self.config.chromium_path

        self.browser = await self._playwright.chromium.launch(**launch_opts)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        await self.stealth.apply_stealth_async(self.context)
        return self

    async def __aexit__(self, *args):
        """Clean up browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def fetch_page(self, url: str, depth: int = 0) -> PageData:
        """Fetch a single page and extract data."""
        page = await self.context.new_page()
        start_time = time.time()

        try:
            # Navigate with timeout
            response = await page.goto(
                url,
                wait_until="networkidle",
                timeout=30000,
            )
            load_time_ms = (time.time() - start_time) * 1000

            # Get page content
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")

            # Extract data
            page_data = PageData(
                url=url,
                depth=depth,
                status_code=response.status if response else None,
                load_time_ms=load_time_ms,
                is_https=url.startswith("https://"),
            )

            # Title
            title_tag = soup.find("title")
            page_data.title = title_tag.get_text(strip=True) if title_tag else None

            # Meta description
            desc_tag = soup.find("meta", attrs={"name": "description"})
            if desc_tag:
                page_data.description = desc_tag.get("content", "")

            # Canonical
            canonical_tag = soup.find("link", attrs={"rel": "canonical"})
            if canonical_tag:
                page_data.canonical = canonical_tag.get("href", "")

            # H1 tags
            page_data.h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all("h1")]

            # Meta tags
            page_data.meta_tags = self._extract_meta_tags(soup)

            # Open Graph
            page_data.og_data = self._extract_og_data(soup)

            # Links
            page_data.links = self._extract_links(soup, url)

            # Images
            page_data.images = self._extract_images(soup, url)

            # Schema types
            page_data.schema_types = self._extract_schema_types(soup)

            # Truncated text content
            body = soup.find("body")
            if body:
                page_data.text_content = body.get_text(separator=" ", strip=True)[:5000]

            if self.verbose:
                print(f"  Fetched: {url} ({load_time_ms:.0f}ms, {len(page_data.links)} links, {len(page_data.images)} images)")

            return page_data

        except Exception as e:
            if self.verbose:
                print(f"  Error fetching {url}: {e}")
            return PageData(
                url=url,
                depth=depth,
                error=str(e),
            )
        finally:
            await page.close()

    def _extract_meta_tags(self, soup: BeautifulSoup) -> list[MetaTag]:
        """Extract all meta tags."""
        tags = []
        for meta in soup.find_all("meta"):
            name = meta.get("name")
            prop = meta.get("property")
            content = meta.get("content", "")
            if name or prop:
                tags.append(MetaTag(name=name, property=prop, content=content))
        return tags

    def _extract_og_data(self, soup: BeautifulSoup) -> Optional[OpenGraphData]:
        """Extract Open Graph metadata."""
        og = {}
        og_mappings = {
            "og:title": "title",
            "og:description": "description",
            "og:image": "image",
            "og:url": "url",
            "og:type": "type",
            "og:site_name": "site_name",
        }
        for meta in soup.find_all("meta", attrs={"property": True}):
            prop = meta.get("property", "")
            if prop in og_mappings:
                og[og_mappings[prop]] = meta.get("content", "")

        if og:
            return OpenGraphData(**og)
        return None

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[LinkData]:
        """Extract all links from the page."""
        links = []
        base_domain = urlparse(base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            # Determine if internal
            is_internal = parsed.netloc == base_domain or not parsed.netloc

            links.append(LinkData(
                href=full_url,
                text=a.get_text(strip=True)[:100],
                is_internal=is_internal,
            ))

        return links

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list[ImageData]:
        """Extract all images from the page."""
        images = []

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src", "")
            if not src:
                continue

            # Resolve relative URLs
            full_src = urljoin(base_url, src)

            # Detect format from URL
            parsed_path = urlparse(full_src).path.lower()
            fmt = None
            for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg"]:
                if parsed_path.endswith(ext):
                    fmt = ext[1:]  # Remove the dot
                    break

            images.append(ImageData(
                src=full_src,
                alt=img.get("alt"),
                width=self._parse_int(img.get("width")),
                height=self._parse_int(img.get("height")),
                format=fmt,
            ))

        return images

    def _extract_schema_types(self, soup: BeautifulSoup) -> list[str]:
        """Extract schema.org types from JSON-LD."""
        types = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    if "@type" in data:
                        types.append(data["@type"])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "@type" in item:
                            types.append(item["@type"])
            except (json.JSONDecodeError, TypeError):
                pass
        return types

    def _parse_int(self, value) -> Optional[int]:
        """Safely parse an integer from string."""
        if value is None:
            return None
        try:
            return int(str(value).replace("px", ""))
        except (ValueError, TypeError):
            return None

    async def pace(self):
        """Apply pacing delay based on config."""
        delay_range = self.config.pacing_delays.get(self.config.pacing, (1, 3))
        if delay_range[0] > 0:
            delay = random.uniform(*delay_range)
            if self.verbose:
                print(f"  Pacing: waiting {delay:.1f}s...")
            await asyncio.sleep(delay)

    async def crawl(
        self,
        start_url: str,
        max_depth: int = 3,
        max_pages: int = 50,
    ) -> list[PageData]:
        """BFS crawl starting from URL, respecting depth and page limits.

        Args:
            start_url: The URL to start crawling from
            max_depth: Maximum link depth to follow (0 = start page only)
            max_pages: Maximum number of pages to crawl

        Returns:
            List of PageData for all crawled pages
        """
        # Normalize the start URL
        parsed_start = urlparse(start_url)
        base_domain = parsed_start.netloc

        # Track visited URLs (normalized)
        visited: set[str] = set()
        # Queue: (url, depth)
        queue: list[tuple[str, int]] = [(start_url, 0)]
        # Results
        pages: list[PageData] = []

        if self.verbose:
            print(f"Starting BFS crawl: max_depth={max_depth}, max_pages={max_pages}")

        while queue and len(pages) < max_pages:
            url, depth = queue.pop(0)

            # Normalize URL for deduplication
            normalized = self._normalize_url(url)
            if normalized in visited:
                continue
            visited.add(normalized)

            # Fetch the page
            if self.verbose:
                print(f"[{len(pages)+1}/{max_pages}] Depth {depth}: {url}")
            elif self.progress_callback:
                self.progress_callback(len(pages) + 1, max_pages, url)

            page_data = await self.fetch_page(url, depth)
            pages.append(page_data)

            # If we haven't reached max depth and page loaded successfully, queue internal links
            if depth < max_depth and not page_data.error:
                for link in page_data.links:
                    if not link.is_internal:
                        continue

                    link_normalized = self._normalize_url(link.href)
                    if link_normalized in visited:
                        continue

                    # Filter out non-page URLs
                    if self._should_skip_url(link.href):
                        continue

                    # Check if same domain
                    link_domain = urlparse(link.href).netloc
                    if link_domain != base_domain:
                        continue

                    queue.append((link.href, depth + 1))

            # Apply pacing between requests (except for first page)
            if len(pages) < max_pages and queue:
                await self.pace()

        if self.verbose:
            successful = sum(1 for p in pages if not p.error)
            print(f"Crawl complete: {len(pages)} pages ({successful} successful)")

        return pages

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        parsed = urlparse(url)
        # Remove fragment, normalize path
        path = parsed.path.rstrip("/") or "/"
        # Lowercase scheme and netloc
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"

    def _should_skip_url(self, url: str) -> bool:
        """Check if URL should be skipped (non-page resources)."""
        parsed = urlparse(url)
        path = parsed.path.lower()

        # Skip common non-page extensions
        skip_extensions = [
            ".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".ico",
            ".css", ".js", ".json", ".xml", ".rss", ".atom",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".zip", ".tar", ".gz", ".rar",
            ".mp3", ".mp4", ".wav", ".avi", ".mov", ".wmv",
            ".woff", ".woff2", ".ttf", ".eot",
        ]
        for ext in skip_extensions:
            if path.endswith(ext):
                return True

        # Skip common non-content paths
        skip_patterns = [
            "/wp-content/uploads/",
            "/wp-includes/",
            "/wp-admin/",
            "/cdn-cgi/",
            "/static/",
            "/assets/",
        ]
        for pattern in skip_patterns:
            if pattern in path:
                return True

        return False
