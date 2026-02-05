"""
Facility Crawler Service

Crawls facility websites and searches for tiger images using FREE tools only:
- DuckDuckGo for facility research and image search (no API key)
- Playwright for direct website crawling (local browser automation)
- Claude web search for intelligent discovery (included in ANTHROPIC_API_KEY)

This service powers the continuous tiger discovery pipeline by:
1. Iterating through TPC reference facilities
2. Crawling their websites for tiger images
3. Searching DuckDuckGo for additional tiger images
4. Passing discovered images to the identification pipeline
"""

import asyncio
import aiohttp
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Any
from uuid import UUID, uuid4
from pathlib import Path
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database.models import Facility, CrawlHistory
from backend.mcp_servers.deep_research_server import get_deep_research_server, HAS_DDGS
from backend.utils.logging import get_logger

# Try to import DuckDuckGo for image search
try:
    from duckduckgo_search import DDGS
    HAS_DDGS_IMAGES = True
except ImportError:
    HAS_DDGS_IMAGES = False

# Try to import Playwright for JS-heavy site crawling
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    PlaywrightTimeoutError = Exception  # Fallback type

logger = get_logger(__name__)


@dataclass
class DiscoveredImage:
    """Represents a discovered tiger image."""
    url: str
    source_url: str
    source_type: str  # 'website', 'duckduckgo', 'search_result'
    facility_id: UUID
    discovered_at: datetime
    metadata: Dict[str, Any]
    content_hash: Optional[str] = None  # SHA256 hash for deduplication


class RateLimiter:
    """
    Per-domain rate limiting with exponential backoff.

    Features:
    - Per-domain request tracking (different sites have different limits)
    - Exponential backoff on rate-limit errors (429, 503, etc.)
    - Gradual recovery on successful requests
    """

    # HTTP status codes that trigger backoff
    BACKOFF_STATUS_CODES = {429, 503, 520, 521, 522, 524}

    def __init__(self, requests_per_second: float = 0.5, max_backoff: float = 60.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Base rate limit (0.5 = 2 seconds between requests)
            max_backoff: Maximum backoff time in seconds
        """
        self._last_request: Dict[str, float] = defaultdict(float)
        self._backoff: Dict[str, float] = defaultdict(lambda: 1.0)
        self._min_interval = 1.0 / requests_per_second
        self._max_backoff = max_backoff
        self._request_count: Dict[str, int] = defaultdict(int)

    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc
        except Exception:
            return "unknown"

    async def wait_for_slot(self, url: str):
        """
        Wait until we can make a request to this domain.

        Args:
            url: The URL we want to request
        """
        domain = self.get_domain(url)
        now = time.time()

        # Calculate required interval based on backoff
        interval = self._min_interval * self._backoff[domain]
        time_since_last = now - self._last_request[domain]
        wait_time = max(0, interval - time_since_last)

        if wait_time > 0:
            logger.debug(f"Rate limiting {domain}: waiting {wait_time:.1f}s (backoff: {self._backoff[domain]:.1f}x)")
            await asyncio.sleep(wait_time)

        self._last_request[domain] = time.time()
        self._request_count[domain] += 1

    def report_error(self, url: str, status_code: int):
        """
        Increase backoff on rate-limit errors.

        Args:
            url: The URL that returned an error
            status_code: HTTP status code
        """
        domain = self.get_domain(url)

        if status_code in self.BACKOFF_STATUS_CODES:
            old_backoff = self._backoff[domain]
            self._backoff[domain] = min(
                self._backoff[domain] * 2,
                self._max_backoff / self._min_interval  # Ensure total wait <= max_backoff
            )
            logger.warning(
                f"Rate limit error from {domain} (HTTP {status_code}). "
                f"Backoff: {old_backoff:.1f}x -> {self._backoff[domain]:.1f}x"
            )
        elif status_code >= 500:
            # Server errors - smaller backoff increase
            self._backoff[domain] = min(
                self._backoff[domain] * 1.5,
                self._max_backoff / self._min_interval
            )
            logger.debug(f"Server error from {domain} (HTTP {status_code}). Backoff: {self._backoff[domain]:.1f}x")

    def report_success(self, url: str):
        """
        Gradually reduce backoff on success.

        Args:
            url: The URL that succeeded
        """
        domain = self.get_domain(url)
        if self._backoff[domain] > 1.0:
            self._backoff[domain] = max(1.0, self._backoff[domain] * 0.9)

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            "domains_tracked": len(self._last_request),
            "total_requests": sum(self._request_count.values()),
            "domains_with_backoff": {
                domain: backoff
                for domain, backoff in self._backoff.items()
                if backoff > 1.0
            }
        }


class FacilityCrawlerService:
    """
    Crawls facility websites and searches for tiger images using FREE tools only.

    No API keys required beyond existing ANTHROPIC_API_KEY.
    """

    # Common image extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}

    # Keywords that suggest tiger-related content
    TIGER_KEYWORDS = {
        'tiger', 'tigers', 'big cat', 'big cats', 'feline', 'panthera tigris',
        'cub', 'cubs', 'bengal', 'siberian', 'sumatran', 'malayan', 'amur',
        'white tiger', 'golden tabby', 'stripey', 'striped'
    }

    # Common gallery page patterns
    GALLERY_PATTERNS = [
        r'/gallery', r'/photos', r'/pictures', r'/animals', r'/tigers',
        r'/residents', r'/our-animals', r'/meet', r'/images', r'/media',
        r'/wildlife', r'/cats', r'/big-cats'
    ]

    # Indicators that a site likely requires JavaScript rendering
    JS_HEAVY_INDICATORS = [
        'react', 'angular', 'vue', '__next_data__', 'webpack',
        'data-reactroot', 'data-reactid', 'ng-app', 'ng-controller',
        '<noscript>', 'loading="lazy"', 'data-src=', 'lazyload',
        '_app.js', '_buildManifest.js', 'window.__NUXT__',
        'window.__INITIAL_STATE__', 'hydrate', 'createRoot'
    ]

    # Minimum indicators needed to classify as JS-heavy
    JS_HEAVY_THRESHOLD = 2

    def __init__(self, db_session: Session):
        """Initialize the facility crawler service."""
        self.db = db_session
        self.deep_research = get_deep_research_server()
        self._session: Optional[aiohttp.ClientSession] = None

        # Per-domain rate limiting with exponential backoff
        self.rate_limiter = RateLimiter(
            requests_per_second=0.5,  # 2 seconds base interval between requests
            max_backoff=60.0  # Maximum wait of 60 seconds
        )

        logger.info(f"FacilityCrawlerService initialized (DuckDuckGo available: {HAS_DDGS_IMAGES})")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
        return self._session

    async def _rate_limit(self, url: str):
        """
        Apply per-domain rate limiting with backoff.

        Args:
            url: The URL about to be requested
        """
        await self.rate_limiter.wait_for_slot(url)

    def _is_js_heavy_site(self, html: str) -> bool:
        """
        Detect if a site likely requires JavaScript rendering.

        Looks for common SPA frameworks, lazy loading, and hydration patterns.

        Args:
            html: The raw HTML content

        Returns:
            True if site appears to need JavaScript rendering
        """
        html_lower = html.lower()
        indicator_count = sum(
            1 for indicator in self.JS_HEAVY_INDICATORS
            if indicator.lower() in html_lower
        )

        is_js_heavy = indicator_count >= self.JS_HEAVY_THRESHOLD

        if is_js_heavy:
            logger.debug(f"JS-heavy site detected ({indicator_count} indicators)")

        return is_js_heavy

    async def _crawl_website_with_playwright(self, facility: Facility) -> List[DiscoveredImage]:
        """
        Crawl JavaScript-heavy sites using Playwright browser automation.

        This handles:
        - Single Page Applications (React, Vue, Angular)
        - Lazy-loaded images
        - Dynamic content that requires JS execution

        Args:
            facility: Facility to crawl

        Returns:
            List of discovered images
        """
        images: List[DiscoveredImage] = []

        if not HAS_PLAYWRIGHT:
            logger.warning("Playwright not available. Install: pip install playwright && playwright install chromium")
            return images

        if not facility.website:
            return images

        logger.info(f"Using Playwright for JS-heavy site: {facility.website}")

        try:
            async with async_playwright() as p:
                # Launch headless browser
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                try:
                    # Navigate to main page
                    await self._rate_limit(facility.website)
                    await page.goto(facility.website, wait_until="networkidle", timeout=30000)

                    # Wait for dynamic content to load
                    await page.wait_for_timeout(2000)

                    # Scroll down to trigger lazy loading
                    for _ in range(3):
                        await page.keyboard.press("End")
                        await page.wait_for_timeout(1000)

                    # Extract images from rendered DOM
                    main_images = await self._extract_images_from_page(page, facility.website)
                    for img_url in main_images:
                        if self._is_potential_tiger_image(img_url):
                            images.append(DiscoveredImage(
                                url=img_url,
                                source_url=facility.website,
                                source_type='website',
                                facility_id=facility.facility_id,
                                discovered_at=datetime.utcnow(),
                                metadata={"page": "main", "renderer": "playwright"}
                            ))

                    # Find gallery links in rendered content
                    gallery_links = await self._find_gallery_links_in_page(page, facility.website)

                    # Visit gallery pages
                    for gallery_url in gallery_links[:5]:
                        try:
                            await self._rate_limit(gallery_url)
                            await page.goto(gallery_url, wait_until="networkidle", timeout=30000)
                            await page.wait_for_timeout(2000)

                            # Scroll for lazy images
                            for _ in range(2):
                                await page.keyboard.press("End")
                                await page.wait_for_timeout(800)

                            gallery_images = await self._extract_images_from_page(page, gallery_url)
                            for img_url in gallery_images:
                                if self._is_potential_tiger_image(img_url):
                                    images.append(DiscoveredImage(
                                        url=img_url,
                                        source_url=gallery_url,
                                        source_type='website',
                                        facility_id=facility.facility_id,
                                        discovered_at=datetime.utcnow(),
                                        metadata={"page": "gallery", "renderer": "playwright"}
                                    ))

                            self.rate_limiter.report_success(gallery_url)

                        except PlaywrightTimeoutError:
                            logger.debug(f"Timeout loading gallery: {gallery_url}")
                            self.rate_limiter.report_error(gallery_url, 408)
                        except Exception as e:
                            logger.debug(f"Failed to crawl gallery {gallery_url}: {e}")
                            self.rate_limiter.report_error(gallery_url, 500)

                    self.rate_limiter.report_success(facility.website)

                except PlaywrightTimeoutError:
                    logger.warning(f"Playwright timeout for {facility.website}")
                    self.rate_limiter.report_error(facility.website, 408)
                finally:
                    await context.close()
                    await browser.close()

        except Exception as e:
            logger.error(f"Playwright crawl failed for {facility.website}: {e}")

        logger.info(f"Playwright found {len(images)} images from {facility.website}")
        return images

    async def _extract_images_from_page(self, page, base_url: str) -> List[str]:
        """
        Extract image URLs from a rendered Playwright page.

        Args:
            page: Playwright page object
            base_url: Base URL for resolving relative paths

        Returns:
            List of absolute image URLs
        """
        images = []

        # Get all img elements with their src and data-src attributes
        img_elements = await page.evaluate("""
            () => {
                const images = [];
                document.querySelectorAll('img').forEach(img => {
                    const src = img.src || img.getAttribute('data-src') ||
                               img.getAttribute('data-lazy-src') || img.getAttribute('data-original');
                    if (src) images.push(src);
                });
                // Also get background images
                document.querySelectorAll('[style*="background"]').forEach(el => {
                    const style = el.style.backgroundImage || '';
                    const match = style.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/);
                    if (match) images.push(match[1]);
                });
                return images;
            }
        """)

        for src in img_elements:
            # Convert relative URLs to absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                parsed = urlparse(base_url)
                src = f"{parsed.scheme}://{parsed.netloc}{src}"
            elif not src.startswith('http'):
                src = urljoin(base_url, src)

            if self._is_valid_image_url(src):
                images.append(src)

        return list(set(images))  # Deduplicate

    async def _find_gallery_links_in_page(self, page, base_url: str) -> List[str]:
        """
        Find gallery/photos links in a rendered Playwright page.

        Args:
            page: Playwright page object
            base_url: Base URL for resolving relative paths

        Returns:
            List of absolute gallery URLs
        """
        links = []

        # Get all anchor hrefs
        hrefs = await page.evaluate("""
            () => {
                const links = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    links.push(a.href);
                });
                return links;
            }
        """)

        for href in hrefs:
            href_lower = href.lower()

            # Check if link matches gallery patterns
            is_gallery = any(
                re.search(pattern, href_lower)
                for pattern in self.GALLERY_PATTERNS
            )

            if is_gallery:
                # Only include links from same domain
                if urlparse(href).netloc == urlparse(base_url).netloc:
                    links.append(href)

        return list(set(links))  # Deduplicate

    def get_facilities_to_crawl(
        self,
        limit: int = 100,
        days_since_last_crawl: int = 7
    ) -> List[Facility]:
        """
        Get facilities that need crawling.

        Prioritizes:
        1. Reference facilities that haven't been crawled
        2. Facilities with high tiger counts
        3. Facilities not crawled recently
        """
        cutoff = datetime.utcnow() - timedelta(days=days_since_last_crawl)

        facilities = self.db.query(Facility).filter(
            Facility.is_reference_facility == True,
            Facility.website.isnot(None),
            or_(
                Facility.last_crawled_at.is_(None),
                Facility.last_crawled_at < cutoff
            )
        ).order_by(
            Facility.last_crawled_at.asc().nulls_first(),
            Facility.tiger_count.desc()
        ).limit(limit).all()

        logger.info(f"Found {len(facilities)} facilities to crawl")
        return facilities

    async def crawl_all_facilities(
        self,
        batch_size: int = 10,
        max_facilities: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Crawl all TPC facilities for tiger images.

        Args:
            batch_size: Number of facilities to crawl in parallel
            max_facilities: Maximum facilities to crawl (None = all)

        Returns:
            Crawl statistics
        """
        facilities = self.get_facilities_to_crawl(limit=max_facilities or 1000)

        stats = {
            "facilities_crawled": 0,
            "images_found": 0,
            "errors": 0,
            "started_at": datetime.utcnow().isoformat()
        }

        for i in range(0, len(facilities), batch_size):
            batch = facilities[i:i + batch_size]

            # Crawl batch in parallel
            tasks = [self.crawl_facility(f) for f in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for facility, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Error crawling {facility.exhibitor_name}: {result}")
                    stats["errors"] += 1
                else:
                    stats["facilities_crawled"] += 1
                    stats["images_found"] += len(result)

            logger.info(f"Crawled batch {i//batch_size + 1}/{(len(facilities) + batch_size - 1)//batch_size}")

        stats["completed_at"] = datetime.utcnow().isoformat()
        return stats

    async def crawl_facility(self, facility: Facility) -> List[DiscoveredImage]:
        """
        Crawl a single facility using FREE tools.

        Args:
            facility: Facility to crawl

        Returns:
            List of discovered images
        """
        logger.info(f"Crawling facility: {facility.exhibitor_name}")

        images: List[DiscoveredImage] = []
        crawl_start = datetime.utcnow()
        error_message = None

        try:
            # 1. DuckDuckGo research for facility context
            await self._research_facility(facility)

            # 2. Crawl facility website
            if facility.website:
                web_images = await self._crawl_website(facility)
                images.extend(web_images)
                logger.info(f"Found {len(web_images)} images from website")

            # 3. Search DuckDuckGo for tiger images
            ddg_images = await self._search_facility_images(facility)
            images.extend(ddg_images)
            logger.info(f"Found {len(ddg_images)} images from DuckDuckGo")

            # Deduplicate by URL
            seen_urls: Set[str] = set()
            unique_images = []
            for img in images:
                if img.url not in seen_urls:
                    seen_urls.add(img.url)
                    unique_images.append(img)
            images = unique_images

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error crawling {facility.exhibitor_name}: {e}")

        # Update facility crawl timestamp
        facility.last_crawled_at = datetime.utcnow()

        # Record crawl history
        crawl_history = CrawlHistory(
            crawl_id=uuid4(),
            facility_id=facility.facility_id,
            source_url=facility.website or "duckduckgo_search",
            status="completed" if not error_message else "failed",
            images_found=len(images),
            crawled_at=crawl_start,
            completed_at=datetime.utcnow(),
            crawl_duration_ms=int((datetime.utcnow() - crawl_start).total_seconds() * 1000),
            error_message=error_message,
            crawl_statistics={
                "website_images": len([i for i in images if i.source_type == 'website']),
                "duckduckgo_images": len([i for i in images if i.source_type == 'duckduckgo']),
                "playwright_rendered": len([i for i in images if i.metadata.get('renderer') == 'playwright']),
                "http_rendered": len([i for i in images if i.source_type == 'website' and i.metadata.get('renderer') != 'playwright'])
            }
        )
        self.db.add(crawl_history)
        self.db.commit()

        logger.info(f"Completed crawl of {facility.exhibitor_name}: {len(images)} images")
        return images

    async def _research_facility(self, facility: Facility) -> Dict:
        """
        Use Deep Research Server (DuckDuckGo) to gather facility intelligence.

        This provides context for better image discovery.
        """
        try:
            result = await self.deep_research._handle_start_research(
                topic=facility.exhibitor_name,
                mode="facility_investigation",
                depth="quick"
            )

            if result.get("success"):
                logger.debug(f"Research found {result.get('results_found', 0)} results for {facility.exhibitor_name}")

            return result

        except Exception as e:
            logger.warning(f"Research failed for {facility.exhibitor_name}: {e}")
            return {}

    async def _crawl_website(self, facility: Facility) -> List[DiscoveredImage]:
        """
        Crawl facility website for tiger images.

        Uses direct HTTP requests by default, with automatic fallback to
        Playwright for JavaScript-heavy sites (SPAs, lazy loading, etc.).
        """
        images: List[DiscoveredImage] = []

        if not facility.website:
            return images

        try:
            await self._rate_limit(facility.website)
            session = await self._get_session()

            # Fetch main page with HTTP first
            async with session.get(facility.website) as response:
                if response.status != 200:
                    self.rate_limiter.report_error(facility.website, response.status)
                    logger.warning(f"Failed to fetch {facility.website}: {response.status}")
                    return images

                self.rate_limiter.report_success(facility.website)
                html = await response.text()

            # Check if this is a JavaScript-heavy site that needs browser rendering
            if self._is_js_heavy_site(html):
                logger.info(f"JS-heavy site detected, switching to Playwright: {facility.website}")
                return await self._crawl_website_with_playwright(facility)

            # Continue with HTTP-based extraction for static sites
            main_images = self._extract_images_from_html(html, facility.website)
            for img_url in main_images:
                if self._is_potential_tiger_image(img_url):
                    images.append(DiscoveredImage(
                        url=img_url,
                        source_url=facility.website,
                        source_type='website',
                        facility_id=facility.facility_id,
                        discovered_at=datetime.utcnow(),
                        metadata={"page": "main"}
                    ))

            # Find and crawl gallery pages
            gallery_links = self._find_gallery_links(html, facility.website)

            for gallery_url in gallery_links[:5]:  # Limit to 5 gallery pages
                try:
                    await self._rate_limit(gallery_url)

                    async with session.get(gallery_url) as response:
                        if response.status == 200:
                            self.rate_limiter.report_success(gallery_url)
                            gallery_html = await response.text()
                            gallery_images = self._extract_images_from_html(gallery_html, gallery_url)

                            for img_url in gallery_images:
                                if self._is_potential_tiger_image(img_url):
                                    images.append(DiscoveredImage(
                                        url=img_url,
                                        source_url=gallery_url,
                                        source_type='website',
                                        facility_id=facility.facility_id,
                                        discovered_at=datetime.utcnow(),
                                        metadata={"page": "gallery"}
                                    ))
                        else:
                            self.rate_limiter.report_error(gallery_url, response.status)
                except Exception as e:
                    self.rate_limiter.report_error(gallery_url, 500)
                    logger.debug(f"Failed to crawl gallery {gallery_url}: {e}")

        except Exception as e:
            logger.warning(f"Website crawl failed for {facility.website}: {e}")

        return images

    def _extract_images_from_html(self, html: str, base_url: str) -> List[str]:
        """Extract image URLs from HTML content."""
        images = []

        # Find all img tags
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        for match in re.finditer(img_pattern, html, re.IGNORECASE):
            src = match.group(1)
            # Convert relative URLs to absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                parsed = urlparse(base_url)
                src = f"{parsed.scheme}://{parsed.netloc}{src}"
            elif not src.startswith('http'):
                src = urljoin(base_url, src)

            # Check if it's an image
            if self._is_valid_image_url(src):
                images.append(src)

        # Also find background images in CSS
        bg_pattern = r'background(?:-image)?:\s*url\(["\']?([^"\')\s]+)["\']?\)'
        for match in re.finditer(bg_pattern, html, re.IGNORECASE):
            src = match.group(1)
            if src.startswith('/'):
                parsed = urlparse(base_url)
                src = f"{parsed.scheme}://{parsed.netloc}{src}"
            elif not src.startswith('http'):
                src = urljoin(base_url, src)

            if self._is_valid_image_url(src):
                images.append(src)

        return images

    def _find_gallery_links(self, html: str, base_url: str) -> List[str]:
        """Find links to potential gallery/photos pages."""
        links = []

        # Find all anchor tags
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\']'

        for match in re.finditer(link_pattern, html, re.IGNORECASE):
            href = match.group(1)
            href_lower = href.lower()

            # Check if link matches gallery patterns
            is_gallery = any(
                re.search(pattern, href_lower)
                for pattern in self.GALLERY_PATTERNS
            )

            if is_gallery:
                # Convert to absolute URL
                if href.startswith('/'):
                    parsed = urlparse(base_url)
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                elif not href.startswith('http'):
                    href = urljoin(base_url, href)

                # Only include links from same domain
                if urlparse(href).netloc == urlparse(base_url).netloc:
                    links.append(href)

        return list(set(links))  # Deduplicate

    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL points to a valid image."""
        try:
            parsed = urlparse(url.lower())
            path = parsed.path

            # Check extension
            return any(path.endswith(ext) for ext in self.IMAGE_EXTENSIONS)
        except:
            return False

    def _is_potential_tiger_image(self, url: str) -> bool:
        """
        Check if URL might contain a tiger image.

        Looks for tiger-related keywords in URL path.
        """
        url_lower = url.lower()

        # Check for tiger keywords in URL
        for keyword in self.TIGER_KEYWORDS:
            if keyword in url_lower:
                return True

        # Also accept generic animal/gallery images (need ML to verify)
        generic_patterns = ['animal', 'wildlife', 'resident', 'cat']
        return any(pattern in url_lower for pattern in generic_patterns)

    async def _search_facility_images(self, facility: Facility) -> List[DiscoveredImage]:
        """
        Search for tiger images using DuckDuckGo image search.

        This is FREE and requires no API key.
        """
        images: List[DiscoveredImage] = []

        if not HAS_DDGS_IMAGES:
            logger.warning("DuckDuckGo search not available. Install: pip install duckduckgo-search")
            return images

        try:
            ddgs = DDGS()

            # Build search queries
            queries = [
                f'"{facility.exhibitor_name}" tiger',
                f'"{facility.exhibitor_name}" tigers',
            ]

            # Add location-based queries
            if facility.city and facility.state:
                queries.append(f'{facility.city} {facility.state} tiger sanctuary')
            elif facility.state:
                queries.append(f'{facility.state} tiger facility')

            for query in queries:
                try:
                    # Rate limit DuckDuckGo API calls
                    await self._rate_limit("https://duckduckgo.com/")

                    # DuckDuckGo image search
                    for result in ddgs.images(query, max_results=10):
                        image_url = result.get("image", "")
                        thumbnail_url = result.get("thumbnail", "")

                        if image_url and self._is_valid_image_url(image_url):
                            images.append(DiscoveredImage(
                                url=image_url,
                                source_url=result.get("url", query),
                                source_type='duckduckgo',
                                facility_id=facility.facility_id,
                                discovered_at=datetime.utcnow(),
                                metadata={
                                    "query": query,
                                    "title": result.get("title", ""),
                                    "thumbnail": thumbnail_url
                                }
                            ))

                    self.rate_limiter.report_success("https://duckduckgo.com/")

                except Exception as e:
                    self.rate_limiter.report_error("https://duckduckgo.com/", 500)
                    logger.debug(f"DuckDuckGo search failed for query '{query}': {e}")

        except Exception as e:
            logger.warning(f"DuckDuckGo image search failed: {e}")

        return images

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()


# Convenience function for getting service instance
def get_facility_crawler_service(db_session: Session) -> FacilityCrawlerService:
    """Create and return a FacilityCrawlerService instance."""
    return FacilityCrawlerService(db_session)
