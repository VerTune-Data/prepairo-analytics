"""
Facebook Ads Library Integration
Fetches competitor ads for analysis
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AdsLibraryClient:
    """Client for Facebook Ads Library API"""

    BASE_URL = "https://graph.facebook.com/v18.0/ads_archive"

    def __init__(self, access_token: str):
        """
        Initialize Ads Library client.

        Args:
            access_token: Facebook access token with ads_read permission
        """
        self.access_token = access_token

    def search_ads(
        self,
        search_terms: str = None,
        ad_reached_countries: List[str] = ['IN'],
        ad_type: str = 'ALL',
        ad_active_status: str = 'ACTIVE',
        limit: int = 50,
        fields: List[str] = None
    ) -> List[Dict]:
        """
        Search for ads in the Facebook Ads Library.

        Args:
            search_terms: Keywords to search for
            ad_reached_countries: Countries where ads were shown (default: India)
            ad_type: Type of ad (ALL, POLITICAL_AND_ISSUE_ADS, etc.)
            ad_active_status: ACTIVE, INACTIVE, or ALL
            limit: Maximum number of results
            fields: Fields to return

        Returns:
            List of ads matching the search criteria
        """
        if fields is None:
            fields = [
                'id',
                'ad_creation_time',
                'ad_creative_bodies',
                'ad_creative_link_captions',
                'ad_creative_link_descriptions',
                'ad_creative_link_titles',
                'ad_delivery_start_time',
                'ad_delivery_stop_time',
                'ad_snapshot_url',
                'currency',
                'page_id',
                'page_name',
                'publisher_platforms',
                'spend',
                'impressions'
            ]

        params = {
            'access_token': self.access_token,
            'ad_reached_countries': ad_reached_countries,
            'ad_type': ad_type,
            'ad_active_status': ad_active_status,
            'limit': limit,
            'fields': ','.join(fields)
        }

        if search_terms:
            params['search_terms'] = search_terms

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            ads = data.get('data', [])
            logger.info(f"Found {len(ads)} ads for search: {search_terms}")
            return ads

        except Exception as e:
            logger.error(f"Ads Library API error: {e}")
            return []

    def get_competitor_ads(
        self,
        competitor_names: List[str],
        country: str = 'IN',
        limit_per_competitor: int = 20
    ) -> Dict[str, List[Dict]]:
        """
        Get ads from multiple competitors.

        Args:
            competitor_names: List of competitor page names or search terms
            country: Country code
            limit_per_competitor: Max ads per competitor

        Returns:
            Dict mapping competitor name to their ads
        """
        results = {}

        for competitor in competitor_names:
            logger.info(f"Fetching ads for competitor: {competitor}")
            ads = self.search_ads(
                search_terms=competitor,
                ad_reached_countries=[country],
                limit=limit_per_competitor
            )
            results[competitor] = ads

        return results

    def analyze_competitor_ads(self, competitor_ads: Dict[str, List[Dict]]) -> Dict:
        """
        Analyze competitor ads and extract insights.

        Args:
            competitor_ads: Dict from get_competitor_ads

        Returns:
            Analysis summary
        """
        analysis = {
            'total_ads': 0,
            'by_competitor': {},
            'common_themes': [],
            'platforms_used': {},
            'creative_formats': []
        }

        all_bodies = []

        for competitor, ads in competitor_ads.items():
            analysis['total_ads'] += len(ads)
            analysis['by_competitor'][competitor] = {
                'ad_count': len(ads),
                'ads': []
            }

            for ad in ads:
                # Extract creative text
                bodies = ad.get('ad_creative_bodies', [])
                all_bodies.extend(bodies)

                # Track platforms
                platforms = ad.get('publisher_platforms', [])
                for platform in platforms:
                    analysis['platforms_used'][platform] = analysis['platforms_used'].get(platform, 0) + 1

                # Store ad summary
                ad_summary = {
                    'page_name': ad.get('page_name'),
                    'headline': ad.get('ad_creative_link_titles', [''])[0] if ad.get('ad_creative_link_titles') else '',
                    'body': bodies[0] if bodies else '',
                    'snapshot_url': ad.get('ad_snapshot_url'),
                    'platforms': platforms,
                    'start_date': ad.get('ad_delivery_start_time')
                }
                analysis['by_competitor'][competitor]['ads'].append(ad_summary)

        return analysis


def get_upsc_competitors() -> List[str]:
    """Get list of UPSC/Education competitors to track"""
    return [
        'SuperKalam',
        'Unacademy',
        'BYJU\'s',
        'Testbook',
        'Adda247',
        'Vision IAS',
        'Drishti IAS',
        'StudyIQ',
        'Oliveboard',
        'Gradeup'
    ]


def format_competitor_insights_for_dashboard(analysis: Dict) -> str:
    """Format competitor analysis as HTML for dashboard"""
    html = """
    <div class="competitor-insights">
        <h3>Competitor Ad Intelligence</h3>
        <p>Based on Facebook Ads Library data</p>

        <div class="competitor-grid">
    """

    for competitor, data in analysis.get('by_competitor', {}).items():
        ad_count = data.get('ad_count', 0)
        html += f"""
        <div class="competitor-card">
            <h4>{competitor}</h4>
            <p>{ad_count} active ads</p>
        """

        # Show top 3 ads
        for ad in data.get('ads', [])[:3]:
            headline = ad.get('headline', 'No headline')[:50]
            html += f"""
            <div class="ad-preview">
                <strong>{headline}</strong>
            </div>
            """

        html += "</div>"

    html += """
        </div>
    </div>
    """

    return html
