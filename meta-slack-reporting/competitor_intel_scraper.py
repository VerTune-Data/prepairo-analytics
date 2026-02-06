#!/usr/bin/env python3
"""
Competitor Ad Intelligence Scraper

Deep scraping of Facebook Ads Library for competitive intelligence.
Extracts creative details, landing pages, and derives strategic insights.

Usage:
    python competitor_intel_scraper.py --competitor superkalam
    python competitor_intel_scraper.py --competitor all --slack
"""

import asyncio
import argparse
import json
import os
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from urllib.parse import urlparse, parse_qs
import requests

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
        "category": "UPSC",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=102666082828113"
    },
    "csewhy": {
        "page_id": "110849375441011",
        "name": "CSEWhy",
        "category": "UPSC",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=110849375441011"
    },
    "prepairo": {
        "page_id": "601408149712039",
        "name": "PrepAiro",
        "category": "UPSC",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=601408149712039"
    },
    "visionias": {
        "page_id": "143599862329279",
        "name": "Vision IAS",
        "category": "UPSC",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=143599862329279"
    },
    "drishtiias": {
        "page_id": "185982271624748",
        "name": "Drishti IAS",
        "category": "UPSC",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=185982271624748"
    },
    "unacademy": {
        "page_id": "1aborar04aborar2aborar8aborar3aborar4aborar0aborar3aborar3aborar3aborar4aborar8aborar7aborar",
        "name": "Unacademy",
        "category": "EdTech",
        "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=1042834033348787"
    }
}

OUTPUT_DIR = Path("competitor_intel")
MEDIA_DIR = OUTPUT_DIR / "media"


class CompetitorIntelScraper:
    """Advanced competitor intelligence scraper."""

    def __init__(self, headless: bool = True, download_media: bool = False):
        self.headless = headless
        self.download_media = download_media
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        """Initialize browser."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US'  # Force English for consistent parsing
        )
        self.page = await self.context.new_page()

    async def stop(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()

    async def scrape_competitor(self, competitor_key: str) -> dict:
        """Full intelligence scrape for a competitor."""
        if competitor_key not in COMPETITORS:
            raise ValueError(f"Unknown competitor: {competitor_key}")

        competitor = COMPETITORS[competitor_key]
        print(f"\n{'='*70}")
        print(f"🔍 INTELLIGENCE SCRAPE: {competitor['name']}")
        print(f"   Category: {competitor['category']} | Page ID: {competitor['page_id']}")
        print(f"{'='*70}")

        result = {
            "competitor": competitor['name'],
            "page_id": competitor['page_id'],
            "category": competitor['category'],
            "scraped_at": datetime.now().isoformat(),
            "url": competitor['url'],
            "summary": {},
            "insights": {},
            "ads": []
        }

        try:
            # Step 1: Load main listing page
            print("\n📄 Loading Ads Library...")
            await self.page.goto(competitor['url'], wait_until='networkidle', timeout=60000)
            await asyncio.sleep(5)

            # Check for no ads
            page_content = await self.page.content()
            if "This Page is not currently running ads" in page_content:
                print("   ⚠️ No active ads found")
                result["summary"]["total_ads"] = 0
                return result

            # Step 2: Scroll to load all ads
            print("📜 Scrolling to load all ads...")
            await self._scroll_to_load_all()

            # Step 3: Extract basic ad list
            print("🔎 Extracting ad data...")
            ads = await self._extract_all_ads()
            print(f"   Found {len(ads)} ads")

            # Step 4: Deep scrape each ad for details
            print("\n📊 Deep scraping individual ads...")
            detailed_ads = []
            for i, ad in enumerate(ads[:30]):  # Limit to 30 for speed
                print(f"   [{i+1}/{min(len(ads), 30)}] Ad {ad['library_id'][:10]}...")
                detailed = await self._scrape_ad_details(ad)
                detailed_ads.append(detailed)
                await asyncio.sleep(0.5)  # Be nice to Facebook

            result["ads"] = detailed_ads

            # Step 5: Generate insights
            print("\n🧠 Generating competitive insights...")
            result["summary"] = self._generate_summary(detailed_ads)
            result["insights"] = self._generate_insights(detailed_ads, competitor['name'])

            # Print insights
            self._print_insights(result)

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            result["error"] = str(e)

        return result

    async def _scroll_to_load_all(self, max_scrolls: int = 50):
        """Scroll to load all ads."""
        last_height = 0
        no_change = 0

        for i in range(max_scrolls):
            current_height = await self.page.evaluate('document.body.scrollHeight')
            if current_height == last_height:
                no_change += 1
                if no_change >= 3:
                    break
            else:
                no_change = 0
                last_height = current_height

            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)

    async def _extract_all_ads(self) -> List[dict]:
        """Extract all ads from the listing page."""
        js_code = """
        () => {
            const ads = [];
            const seenIds = new Set();

            // Find all Library ID patterns
            const bodyText = document.body.innerText;
            const idMatches = bodyText.matchAll(/ID[:\\s]*([\\d]{10,20})/gi);

            for (const match of idMatches) {
                const adId = match[1];
                if (!seenIds.has(adId)) {
                    seenIds.add(adId);
                    ads.push({
                        library_id: adId,
                        ad_url: `https://www.facebook.com/ads/library/?id=${adId}`
                    });
                }
            }

            return ads;
        }
        """
        return await self.page.evaluate(js_code)

    async def _scrape_ad_details(self, ad: dict) -> dict:
        """Scrape detailed information from individual ad page."""
        detailed = {
            **ad,
            "start_date": None,
            "days_running": None,
            "status": "active",
            "platforms": [],
            "ad_text": None,
            "cta_type": None,
            "landing_url": None,
            "landing_domain": None,
            "media_type": None,
            "media_urls": [],
            "has_video": False,
            "has_carousel": False,
            "variations_count": 1
        }

        try:
            # Navigate to ad detail page
            await self.page.goto(ad['ad_url'], wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # Extract all details via JavaScript
            details = await self.page.evaluate("""
            () => {
                const result = {
                    text: '',
                    startDate: null,
                    platforms: [],
                    ctaType: null,
                    landingUrl: null,
                    hasVideo: false,
                    hasCarousel: false,
                    mediaUrls: [],
                    variationsCount: 1
                };

                // Get all text content
                const allText = document.body.innerText;
                result.text = allText;

                // Find start date patterns
                const datePatterns = [
                    /Started running on ([A-Za-z]+ \\d+, \\d{4})/,
                    /Started running on (\\d{1,2} [A-Za-z]+ \\d{4})/,
                    /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s+\\d{1,2},\\s+\\d{4}/i
                ];
                for (const pattern of datePatterns) {
                    const match = allText.match(pattern);
                    if (match) {
                        result.startDate = match[1] || match[0];
                        break;
                    }
                }

                // Detect platforms
                if (allText.includes('Facebook') || document.querySelector('[aria-label*="Facebook"]')) {
                    result.platforms.push('facebook');
                }
                if (allText.includes('Instagram') || document.querySelector('[aria-label*="Instagram"]')) {
                    result.platforms.push('instagram');
                }
                if (allText.includes('Messenger')) result.platforms.push('messenger');
                if (allText.includes('Audience Network')) result.platforms.push('audience_network');

                // Find CTA buttons
                const ctaPatterns = ['Install Now', 'Learn More', 'Shop Now', 'Sign Up', 'Download', 'Get Offer', 'Book Now', 'Contact Us', 'Apply Now', 'Subscribe'];
                for (const cta of ctaPatterns) {
                    if (allText.includes(cta)) {
                        result.ctaType = cta;
                        break;
                    }
                }

                // Find landing URLs
                const links = document.querySelectorAll('a[href*="l.facebook.com"], a[href*="play.google.com"], a[href*="apps.apple.com"], a[role="link"]');
                links.forEach(link => {
                    const href = link.href;
                    if (href && !href.includes('facebook.com/ads/library') && !href.includes('facebook.com/privacy')) {
                        // Try to extract actual URL from Facebook redirect
                        if (href.includes('l.facebook.com')) {
                            const urlMatch = href.match(/u=([^&]+)/);
                            if (urlMatch) {
                                result.landingUrl = decodeURIComponent(urlMatch[1]);
                            }
                        } else {
                            result.landingUrl = href;
                        }
                    }
                });

                // Check for video
                result.hasVideo = document.querySelectorAll('video').length > 0;

                // Check for carousel (multiple images)
                const images = document.querySelectorAll('img[src*="scontent"]');
                result.hasCarousel = images.length > 2;

                // Get media URLs
                images.forEach(img => {
                    if (img.src && img.src.includes('scontent')) {
                        result.mediaUrls.push(img.src);
                    }
                });

                // Count variations
                const variationText = allText.match(/(\\d+) ads? use this creative/);
                if (variationText) {
                    result.variationsCount = parseInt(variationText[1]);
                }

                return result;
            }
            """)

            # Parse and assign details
            detailed["platforms"] = details.get("platforms", [])
            detailed["cta_type"] = details.get("ctaType")
            detailed["has_video"] = details.get("hasVideo", False)
            detailed["has_carousel"] = details.get("hasCarousel", False)
            detailed["media_urls"] = details.get("mediaUrls", [])[:3]  # Limit
            detailed["variations_count"] = details.get("variationsCount", 1)
            detailed["media_type"] = "video" if detailed["has_video"] else ("carousel" if detailed["has_carousel"] else "image")

            # Parse landing URL
            if details.get("landingUrl"):
                detailed["landing_url"] = details["landingUrl"]
                try:
                    parsed = urlparse(details["landingUrl"])
                    detailed["landing_domain"] = parsed.netloc
                except:
                    pass

            # Parse start date and calculate days running
            if details.get("startDate"):
                detailed["start_date"] = details["startDate"]
                try:
                    # Try multiple date formats
                    for fmt in ["%b %d, %Y", "%d %b %Y", "%B %d, %Y"]:
                        try:
                            start = datetime.strptime(details["startDate"], fmt)
                            detailed["days_running"] = (datetime.now() - start).days
                            break
                        except:
                            continue
                except:
                    pass

            # Extract ad text (clean it up)
            full_text = details.get("text", "")
            # Find the actual ad copy (usually after page name, before CTA)
            ad_text_match = re.search(r'(?:PrepAiro|SuperKalam|Unacademy|Vision IAS|Drishti IAS|CSEWhy)[^\n]*\n([^\n]{20,500})', full_text)
            if ad_text_match:
                detailed["ad_text"] = ad_text_match.group(1).strip()
            else:
                # Fallback: find substantial text blocks
                text_blocks = re.findall(r'[A-Za-z][^.!?]*[.!?]', full_text)
                substantial = [t for t in text_blocks if len(t) > 50 and len(t) < 500]
                if substantial:
                    detailed["ad_text"] = substantial[0].strip()

        except Exception as e:
            detailed["error"] = str(e)

        return detailed

    def _generate_summary(self, ads: List[dict]) -> dict:
        """Generate summary statistics."""
        summary = {
            "total_ads": len(ads),
            "with_video": sum(1 for a in ads if a.get("has_video")),
            "with_carousel": sum(1 for a in ads if a.get("has_carousel")),
            "image_only": sum(1 for a in ads if a.get("media_type") == "image"),
            "platforms": {},
            "cta_types": {},
            "landing_domains": {},
            "avg_days_running": 0,
            "new_ads_7d": 0,
            "long_running_30d": 0
        }

        days_running = []
        for ad in ads:
            # Platforms
            for p in ad.get("platforms", []):
                summary["platforms"][p] = summary["platforms"].get(p, 0) + 1

            # CTA types
            cta = ad.get("cta_type") or "Unknown"
            summary["cta_types"][cta] = summary["cta_types"].get(cta, 0) + 1

            # Landing domains
            domain = ad.get("landing_domain") or "Unknown"
            summary["landing_domains"][domain] = summary["landing_domains"].get(domain, 0) + 1

            # Days running
            if ad.get("days_running") is not None:
                days_running.append(ad["days_running"])
                if ad["days_running"] <= 7:
                    summary["new_ads_7d"] += 1
                if ad["days_running"] >= 30:
                    summary["long_running_30d"] += 1

        if days_running:
            summary["avg_days_running"] = round(sum(days_running) / len(days_running), 1)

        return summary

    def _generate_insights(self, ads: List[dict], competitor_name: str) -> dict:
        """Generate strategic insights."""
        insights = {
            "strategy_signals": [],
            "creative_patterns": [],
            "messaging_themes": [],
            "recommendations": []
        }

        summary = self._generate_summary(ads)

        # Strategy signals
        if summary["with_video"] > summary["total_ads"] * 0.5:
            insights["strategy_signals"].append(f"🎬 Video-heavy strategy ({summary['with_video']}/{summary['total_ads']} ads use video)")
        elif summary["with_video"] == 0:
            insights["strategy_signals"].append("📷 Image-only strategy (no video ads)")

        if summary["new_ads_7d"] > 5:
            insights["strategy_signals"].append(f"🚀 Aggressive testing phase ({summary['new_ads_7d']} new ads in last 7 days)")

        if summary["long_running_30d"] > 0:
            insights["strategy_signals"].append(f"⭐ {summary['long_running_30d']} 'evergreen' ads running 30+ days (likely winners)")

        # Platform strategy
        fb_count = summary["platforms"].get("facebook", 0)
        ig_count = summary["platforms"].get("instagram", 0)
        if ig_count > fb_count * 2:
            insights["strategy_signals"].append("📱 Instagram-focused targeting")
        elif fb_count > ig_count * 2:
            insights["strategy_signals"].append("💻 Facebook-focused targeting")

        # CTA patterns
        top_cta = max(summary["cta_types"].items(), key=lambda x: x[1], default=("Unknown", 0))
        if top_cta[0] != "Unknown":
            insights["creative_patterns"].append(f"Primary CTA: '{top_cta[0]}' ({top_cta[1]} ads)")

        # Landing page insights
        domains = summary["landing_domains"]
        if "play.google.com" in domains or any("play.google" in d for d in domains):
            insights["creative_patterns"].append("🤖 Driving Android app installs")
        if "apps.apple.com" in domains or any("apple.com" in d for d in domains):
            insights["creative_patterns"].append("🍎 Driving iOS app installs")

        # Extract messaging themes from ad text
        all_text = " ".join([a.get("ad_text", "") or "" for a in ads]).lower()
        themes = {
            "pricing/offers": ["free", "₹", "rs", "discount", "offer", "cheap"],
            "urgency": ["limited", "hurry", "now", "today", "last chance"],
            "social proof": ["toppers", "rank", "students", "success", "result"],
            "fear/motivation": ["don't miss", "prelims", "mains", "crack", "clear"]
        }
        for theme, keywords in themes.items():
            if any(kw in all_text for kw in keywords):
                insights["messaging_themes"].append(theme)

        # Recommendations
        if summary["long_running_30d"] > 0:
            long_runners = [a for a in ads if a.get("days_running", 0) >= 30]
            insights["recommendations"].append(f"Study their {len(long_runners)} long-running ads for winning creative patterns")

        if summary["with_video"] > summary["total_ads"] * 0.3:
            insights["recommendations"].append("Consider increasing video content in your ads")

        return insights

    def _print_insights(self, result: dict):
        """Print insights to console."""
        print(f"\n{'='*70}")
        print(f"📊 COMPETITIVE INTELLIGENCE REPORT: {result['competitor']}")
        print(f"{'='*70}")

        s = result["summary"]
        print(f"\n📈 SUMMARY")
        print(f"   Total Active Ads: {s['total_ads']}")
        print(f"   Media Mix: {s['with_video']} video, {s['with_carousel']} carousel, {s['image_only']} image")
        print(f"   Avg Days Running: {s['avg_days_running']}")
        print(f"   New (≤7 days): {s['new_ads_7d']} | Evergreen (30+ days): {s['long_running_30d']}")

        print(f"\n🎯 PLATFORMS")
        for p, count in s['platforms'].items():
            print(f"   {p}: {count} ads")

        print(f"\n🔘 CTA TYPES")
        for cta, count in sorted(s['cta_types'].items(), key=lambda x: -x[1])[:5]:
            print(f"   {cta}: {count}")

        i = result["insights"]
        if i["strategy_signals"]:
            print(f"\n🧠 STRATEGY SIGNALS")
            for signal in i["strategy_signals"]:
                print(f"   {signal}")

        if i["messaging_themes"]:
            print(f"\n💬 MESSAGING THEMES: {', '.join(i['messaging_themes'])}")

        if i["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS")
            for rec in i["recommendations"]:
                print(f"   • {rec}")

        # Show top performing ads (longest running)
        long_runners = sorted([a for a in result["ads"] if a.get("days_running")],
                             key=lambda x: x.get("days_running", 0), reverse=True)[:3]
        if long_runners:
            print(f"\n⭐ TOP PERFORMING ADS (longest running)")
            for ad in long_runners:
                print(f"   • {ad['library_id']} - {ad.get('days_running', '?')} days")
                if ad.get('ad_text'):
                    print(f"     \"{ad['ad_text'][:100]}...\"")
                print(f"     {ad['ad_url']}")


async def main():
    parser = argparse.ArgumentParser(description='Competitor Ad Intelligence Scraper')
    parser.add_argument('--competitor', '-c', type=str, required=True,
                       help=f'Competitor: {", ".join(COMPETITORS.keys())}, or "all"')
    parser.add_argument('--no-headless', action='store_true',
                       help='Show browser window')
    parser.add_argument('--download-media', action='store_true',
                       help='Download ad images/videos')
    parser.add_argument('--output', '-o', type=str,
                       help='Output JSON file')

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    if args.download_media:
        MEDIA_DIR.mkdir(exist_ok=True)

    scraper = CompetitorIntelScraper(
        headless=not args.no_headless,
        download_media=args.download_media
    )

    try:
        await scraper.start()

        results = []
        competitors = list(COMPETITORS.keys()) if args.competitor == 'all' else [args.competitor]

        for comp in competitors:
            result = await scraper.scrape_competitor(comp)
            results.append(result)

            # Save individual result
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = OUTPUT_DIR / f"{comp}_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Saved: {output_file}")

            if len(competitors) > 1:
                await asyncio.sleep(3)

        # Save combined if multiple
        if len(results) > 1:
            combined_file = OUTPUT_DIR / f"all_competitors_{timestamp}.json"
            with open(combined_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Combined report: {combined_file}")

    finally:
        await scraper.stop()


if __name__ == '__main__':
    asyncio.run(main())
