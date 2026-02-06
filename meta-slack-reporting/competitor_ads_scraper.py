#!/usr/bin/env python3
"""
Facebook Ads Library Scraper

Scrapes competitor ads from Facebook Ads Library website since the API
doesn't expose commercial UPSC/education ads for India.

Usage:
    python competitor_ads_scraper.py --competitor superkalam
    python competitor_ads_scraper.py --competitor all
    python competitor_ads_scraper.py --page-id 102666082828113
"""

import asyncio
import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    exit(1)

# Competitor configurations
COMPETITORS = {
    "superkalam": {
        "page_id": "102666082828113",
        "name": "SuperKalam",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=102666082828113"
    },
    "csewhy": {
        "page_id": "61559687599072",
        "name": "CSEWhy",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=61559687599072"
    },
    "prepairo": {
        "page_id": "601408149712039",
        "name": "PrepAiro",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=601408149712039"
    },
    "visionias": {
        "page_id": "143599862329279",
        "name": "Vision IAS",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=143599862329279"
    },
    "drishtiias": {
        "page_id": "185982271624748",
        "name": "Drishti IAS",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=185982271624748"
    }
}

OUTPUT_DIR = Path("competitor_ads_data")


class AdsLibraryScraper:
    """Scrapes Facebook Ads Library for competitor ad intelligence."""

    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        """Initialize browser."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()

    async def stop(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()

    async def scrape_competitor(self, competitor_key: str) -> dict:
        """Scrape ads for a specific competitor."""
        if competitor_key not in COMPETITORS:
            raise ValueError(f"Unknown competitor: {competitor_key}. Available: {list(COMPETITORS.keys())}")

        competitor = COMPETITORS[competitor_key]
        print(f"\n{'='*60}")
        print(f"Scraping: {competitor['name']} (Page ID: {competitor['page_id']})")
        print(f"{'='*60}")

        return await self._scrape_page(competitor['url'], competitor['name'], competitor_key)

    async def scrape_by_page_id(self, page_id: str, name: str = "Unknown") -> dict:
        """Scrape ads for a specific page ID."""
        url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id={page_id}"
        print(f"\n{'='*60}")
        print(f"Scraping Page ID: {page_id} ({name})")
        print(f"{'='*60}")

        return await self._scrape_page(url, name, page_id)

    async def _scrape_page(self, url: str, name: str, identifier: str) -> dict:
        """Core scraping logic for an Ads Library page."""
        result = {
            "name": name,
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "total_ads": 0,
            "ads": []
        }

        try:
            # Navigate to page
            print(f"Loading page...")
            await self.page.goto(url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(5)  # Let dynamic content fully load

            # Take debug screenshot
            if self.debug:
                OUTPUT_DIR.mkdir(exist_ok=True)
                screenshot_path = OUTPUT_DIR / f"{identifier}_debug.png"
                await self.page.screenshot(path=str(screenshot_path), full_page=False)
                print(f"  Debug screenshot saved: {screenshot_path}")

            # Check for "no ads" message
            page_text = await self.page.content()
            if "This Page is not currently running ads" in page_text:
                print(f"No active ads found for {name}")
                return result

            # Get ad count from page header if available
            try:
                ad_count_text = await self.page.locator('text=/\\d+ ads? use this/i').first.text_content(timeout=5000)
                if ad_count_text:
                    print(f"  Page shows: {ad_count_text}")
            except:
                pass

            # Scroll to load all ads
            print("Scrolling to load all ads...")
            ads_loaded = await self._scroll_and_load_ads()
            print(f"Scrolling complete")

            # Extract ads using JavaScript
            ads = await self._extract_ads_via_js()
            result["ads"] = ads
            result["total_ads"] = len(ads)

            print(f"\nExtracted {len(ads)} ads for {name}")

            # Print summary
            if ads:
                print("\nAd Summary:")
                for i, ad in enumerate(ads[:5], 1):
                    print(f"  {i}. Library ID: {ad.get('library_id', 'N/A')}")
                    print(f"     Started: {ad.get('start_date', 'N/A')}")
                    text_preview = ad.get('text_preview', 'N/A') or 'N/A'
                    print(f"     Text: {text_preview[:80]}...")
                    print()
                if len(ads) > 5:
                    print(f"  ... and {len(ads) - 5} more ads")

        except Exception as e:
            print(f"Error scraping {name}: {str(e)}")
            result["error"] = str(e)
            if self.debug:
                import traceback
                traceback.print_exc()

        return result

    async def _scroll_and_load_ads(self, max_scrolls: int = 30) -> int:
        """Scroll page to load all ads (infinite scroll)."""
        last_height = 0
        no_change_count = 0

        for i in range(max_scrolls):
            # Get current scroll height
            current_height = await self.page.evaluate('document.body.scrollHeight')

            if current_height == last_height:
                no_change_count += 1
                if no_change_count >= 3:
                    break
            else:
                no_change_count = 0
                last_height = current_height

            # Scroll down
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1.5)

            if (i + 1) % 5 == 0:
                print(f"  Scroll {i+1}...")

        return 0  # Count determined by extraction

    async def _extract_ads_via_js(self) -> list:
        """Extract ad data using JavaScript for reliability."""

        # JavaScript to extract all ad library IDs and data from the page
        # Handles multiple languages (English, Kannada, Hindi, etc.)
        js_code = """
        () => {
            const ads = [];
            const seenIds = new Set();

            // Method 1: Find all links containing ad library IDs (multiple URL patterns)
            const linkSelectors = [
                'a[href*="/ads/library/?id="]',
                'a[href*="ads/library?id="]',
                'a[href*="id="][href*="library"]'
            ];

            linkSelectors.forEach(selector => {
                const links = document.querySelectorAll(selector);
                links.forEach(link => {
                    const href = link.getAttribute('href');
                    const match = href.match(/[?&]id=(\\d+)/);
                    if (match && !seenIds.has(match[1])) {
                        const adId = match[1];
                        seenIds.add(adId);

                        // Try to find the parent ad container
                        let container = link.closest('div[class*="x1dr59a3"]') ||
                                       link.closest('div[role="article"]') ||
                                       link.parentElement?.parentElement?.parentElement?.parentElement;

                        let textContent = '';
                        let startDate = null;
                        let platforms = [];

                        if (container) {
                            textContent = container.textContent || '';

                            // Extract start date (multiple patterns/languages)
                            const datePatterns = [
                                /Started running on ([A-Za-z]+ \\d+, \\d+)/,
                                /(\\w+ \\d+, \\d{4}).*ಗಂಟೆಗಳು/,  // Kannada
                                /(\\d{1,2} [A-Za-z]+ \\d{4})/
                            ];
                            for (const pattern of datePatterns) {
                                const dateMatch = textContent.match(pattern);
                                if (dateMatch) {
                                    startDate = dateMatch[1];
                                    break;
                                }
                            }

                            // Extract platforms (check for icons or text)
                            if (textContent.includes('Facebook') || container.innerHTML.includes('facebook')) platforms.push('facebook');
                            if (textContent.includes('Instagram') || container.innerHTML.includes('instagram')) platforms.push('instagram');
                            if (textContent.includes('Messenger') || container.innerHTML.includes('messenger')) platforms.push('messenger');
                            if (textContent.includes('Audience Network')) platforms.push('audience_network');
                        }

                        ads.push({
                            library_id: adId,
                            ad_url: 'https://www.facebook.com' + (href.startsWith('/') ? href : '/' + href),
                            start_date: startDate,
                            platforms: platforms,
                            text_preview: textContent.substring(0, 500)
                        });
                    }
                });
            });

            // Method 2: Find Library IDs in text (multiple languages)
            // Patterns: "Library ID: 123", "ಲೈಬ್ರರಿ ID: 123", etc.
            const allText = document.body.innerText;
            const idPatterns = [
                /Library ID[:\\s]+([\\d]+)/gi,
                /ಲೈಬ್ರರಿ ID[:\\s]+([\\d]+)/gi,  // Kannada
                /लाइब्रेरी ID[:\\s]+([\\d]+)/gi,  // Hindi
                /ID[:\\s]+([\\d]{10,})/gi  // Generic long number after ID
            ];

            idPatterns.forEach(pattern => {
                let match;
                while ((match = pattern.exec(allText)) !== null) {
                    const adId = match[1];
                    if (adId && adId.length >= 10 && !seenIds.has(adId)) {
                        seenIds.add(adId);
                        ads.push({
                            library_id: adId,
                            ad_url: `https://www.facebook.com/ads/library/?id=${adId}`,
                            start_date: null,
                            platforms: [],
                            text_preview: null
                        });
                    }
                }
            });

            // Method 3: Find ad cards by looking for specific patterns
            // Each ad card usually has a container with the Library ID text
            const allDivs = document.querySelectorAll('div');
            allDivs.forEach(div => {
                const text = div.textContent || '';
                // Look for Library ID patterns with 10+ digit numbers
                const idMatch = text.match(/ID[:\\s]*([\\d]{10,20})/);
                if (idMatch && !seenIds.has(idMatch[1])) {
                    const adId = idMatch[1];
                    // Verify it looks like an ad card (has PrepAiro or similar content)
                    if (text.length > 50 && text.length < 2000) {
                        seenIds.add(adId);

                        let platforms = [];
                        if (text.includes('Facebook') || div.innerHTML.includes('facebook')) platforms.push('facebook');
                        if (text.includes('Instagram') || div.innerHTML.includes('instagram')) platforms.push('instagram');

                        ads.push({
                            library_id: adId,
                            ad_url: `https://www.facebook.com/ads/library/?id=${adId}`,
                            start_date: null,
                            platforms: platforms,
                            text_preview: text.substring(0, 500)
                        });
                    }
                }
            });

            return ads;
        }
        """

        ads = await self.page.evaluate(js_code)

        # Clean up text previews
        for ad in ads:
            if ad.get('text_preview'):
                # Remove excessive whitespace and newlines
                text = ad['text_preview']
                text = ' '.join(text.split())
                # Remove common header text
                for remove in ['See ad details', 'Library ID', 'Started running on', 'Active']:
                    text = text.replace(remove, '')
                ad['text_preview'] = text.strip()[:300] if text else None

        return ads


async def main():
    parser = argparse.ArgumentParser(description='Scrape Facebook Ads Library for competitor ads')
    parser.add_argument('--competitor', '-c', type=str,
                       help=f'Competitor to scrape: {", ".join(COMPETITORS.keys())}, or "all"')
    parser.add_argument('--page-id', '-p', type=str,
                       help='Specific page ID to scrape')
    parser.add_argument('--name', '-n', type=str, default='Unknown',
                       help='Name for the page (used with --page-id)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_true',
                       help='Run browser with visible UI (for debugging)')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Enable debug mode (saves screenshots)')
    parser.add_argument('--output', '-o', type=str,
                       help='Output JSON file path')

    args = parser.parse_args()

    # Validate args
    if not args.competitor and not args.page_id:
        print("Error: Must specify either --competitor or --page-id")
        print(f"Available competitors: {', '.join(COMPETITORS.keys())}")
        return

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Initialize scraper
    headless = not args.no_headless
    scraper = AdsLibraryScraper(headless=headless, debug=args.debug)

    try:
        await scraper.start()

        results = []

        if args.page_id:
            # Scrape specific page ID
            result = await scraper.scrape_by_page_id(args.page_id, args.name)
            results.append(result)

        elif args.competitor == 'all':
            # Scrape all competitors
            for key in COMPETITORS.keys():
                result = await scraper.scrape_competitor(key)
                results.append(result)
                await asyncio.sleep(2)  # Be nice to Facebook

        else:
            # Scrape specific competitor
            result = await scraper.scrape_competitor(args.competitor)
            results.append(result)

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if args.output:
            output_file = Path(args.output)
        else:
            if len(results) == 1:
                name = results[0]['name'].lower().replace(' ', '_')
                output_file = OUTPUT_DIR / f"{name}_{timestamp}.json"
            else:
                output_file = OUTPUT_DIR / f"all_competitors_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(results if len(results) > 1 else results[0], f, indent=2)

        print(f"\n{'='*60}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*60}")

        # Print summary
        print("\n📊 SCRAPING SUMMARY")
        print("-" * 40)
        total_ads = 0
        for r in results:
            count = r.get('total_ads', 0)
            total_ads += count
            status = "✅" if count > 0 else "⚠️"
            print(f"{status} {r['name']}: {count} ads")
        print("-" * 40)
        print(f"Total: {total_ads} ads from {len(results)} page(s)")

    finally:
        await scraper.stop()


if __name__ == '__main__':
    asyncio.run(main())
