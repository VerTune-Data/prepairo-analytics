"""
HTML Dashboard Generator for Meta Ads Reports
Uses Claude AI to dynamically generate beautiful HTML dashboards with insights
"""

import json
import logging
from typing import Dict
from datetime import datetime

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Generate HTML dashboards for Meta Ads reports using Claude AI"""

    def __init__(self, api_key: str, model: str = 'claude-opus-4-5-20251101'):
        """
        Initialize the dashboard generator with Claude AI.

        Args:
            api_key: Anthropic API key
            model: Claude model to use for generation
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate_dashboard(self, snapshot_data: Dict, deltas: Dict, account_name: str, competitor_intel: Dict = None) -> str:
        """
        Generate HTML dashboard using Claude AI.

        Args:
            snapshot_data: Current campaign/adset/ad data with metrics
            deltas: Changes from previous period
            account_name: Name of the ad account
            competitor_intel: Optional competitor intelligence data from scraper

        Returns:
            Complete HTML string for the dashboard
        """
        # Prepare the data for Claude
        prompt = self._build_prompt(snapshot_data, deltas, account_name, competitor_intel)

        try:
            # Call Claude to generate the dashboard
            response = self.client.messages.create(
                model=self.model,
                max_tokens=64000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract HTML from response
            html_content = response.content[0].text

            # Clean up if Claude wrapped in markdown code blocks
            if html_content.startswith("```html"):
                html_content = html_content[7:]
            if html_content.startswith("```"):
                html_content = html_content[3:]
            if html_content.endswith("```"):
                html_content = html_content[:-3]

            html_content = html_content.strip()

            logger.info(f"Dashboard generated successfully for {account_name}")
            return html_content

        except Exception as e:
            logger.error(f"Error generating dashboard with Claude: {e}")
            # Return a fallback error dashboard
            return self._generate_error_dashboard(account_name, str(e))

    def _build_prompt(self, snapshot_data: Dict, deltas: Dict, account_name: str, competitor_intel: Dict = None) -> str:
        """Build the prompt for Claude to generate the dashboard."""

        campaigns = snapshot_data.get('campaigns', [])
        adsets = snapshot_data.get('adsets', [])
        ads = snapshot_data.get('ads', [])
        balance = snapshot_data.get('balance', {})
        date_since = snapshot_data.get('date_since', datetime.now().strftime('%Y-%m-%d'))

        # Prepare ALL ACTIVE campaign data with ALL conversion types (filter out paused)
        campaigns_summary = []
        for c in campaigns:
            if c.get('effective_status') != 'ACTIVE':
                continue  # Skip paused/inactive campaigns
            parsed = c.get('parsed_actions', {})
            installs = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or 0)
            registrations = int(parsed.get('omni_complete_registration', 0) or parsed.get('complete_registration', 0) or 0)
            checkouts = int(parsed.get('omni_initiated_checkout', 0) or parsed.get('initiated_checkout', 0) or 0)
            purchases = int(parsed.get('omni_purchase', 0) or parsed.get('purchase', 0) or 0)
            spend = float(c.get('spend', 0))
            campaigns_summary.append({
                'name': c.get('campaign_name', 'Unknown'),
                'spend': spend,
                'impressions': int(c.get('impressions', 0)),
                'clicks': int(c.get('clicks', 0)),
                'installs': installs,
                'registrations': registrations,
                'checkouts': checkouts,
                'purchases': purchases,
                'cpi': round(spend / installs, 2) if installs > 0 else 0,
                'cpr': round(spend / registrations, 2) if registrations > 0 else 0,
                'cpa': round(spend / purchases, 2) if purchases > 0 else 0,
                'status': c.get('effective_status', 'UNKNOWN')
            })

        # Prepare ALL ACTIVE adset data (filter out paused)
        adsets_summary = []
        for a in adsets:
            if a.get('effective_status') != 'ACTIVE':
                continue  # Skip paused/inactive adsets
            parsed = a.get('parsed_actions', {})
            installs = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or 0)
            registrations = int(parsed.get('omni_complete_registration', 0) or parsed.get('complete_registration', 0) or 0)
            checkouts = int(parsed.get('omni_initiated_checkout', 0) or parsed.get('initiated_checkout', 0) or 0)
            purchases = int(parsed.get('omni_purchase', 0) or parsed.get('purchase', 0) or 0)
            spend = float(a.get('spend', 0))
            adsets_summary.append({
                'name': a.get('adset_name', 'Unknown'),
                'campaign': a.get('campaign_name', 'Unknown'),
                'spend': spend,
                'impressions': int(a.get('impressions', 0)),
                'clicks': int(a.get('clicks', 0)),
                'installs': installs,
                'registrations': registrations,
                'checkouts': checkouts,
                'purchases': purchases,
                'cpi': round(spend / installs, 2) if installs > 0 else 0,
                'cpr': round(spend / registrations, 2) if registrations > 0 else 0,
                'cpa': round(spend / purchases, 2) if purchases > 0 else 0,
                'status': a.get('effective_status', 'UNKNOWN')
            })

        # Prepare ALL ACTIVE ad data (filter out paused)
        ads_summary = []
        for a in ads:
            if a.get('effective_status') != 'ACTIVE':
                continue  # Skip paused/inactive ads
            parsed = a.get('parsed_actions', {})
            installs = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or 0)
            registrations = int(parsed.get('omni_complete_registration', 0) or parsed.get('complete_registration', 0) or 0)
            checkouts = int(parsed.get('omni_initiated_checkout', 0) or parsed.get('initiated_checkout', 0) or 0)
            purchases = int(parsed.get('omni_purchase', 0) or parsed.get('purchase', 0) or 0)
            spend = float(a.get('spend', 0))
            ads_summary.append({
                'name': a.get('ad_name', 'Unknown'),
                'adset': a.get('adset_name', 'Unknown'),
                'campaign': a.get('campaign_name', 'Unknown'),
                'spend': spend,
                'impressions': int(a.get('impressions', 0)),
                'clicks': int(a.get('clicks', 0)),
                'ctr': round(float(a.get('ctr', 0)), 2),
                'installs': installs,
                'registrations': registrations,
                'checkouts': checkouts,
                'purchases': purchases,
                'cpi': round(spend / installs, 2) if installs > 0 else 0,
                'status': a.get('effective_status', 'UNKNOWN')
            })

        # Calculate totals and derived metrics
        total_spend = sum(c.get('spend', 0) for c in campaigns_summary)
        total_impressions = sum(c.get('impressions', 0) for c in campaigns_summary)
        total_clicks = sum(c.get('clicks', 0) for c in campaigns_summary)
        total_installs = sum(c.get('installs', 0) for c in campaigns_summary)
        total_registrations = sum(c.get('registrations', 0) for c in campaigns_summary)
        total_checkouts = sum(c.get('checkouts', 0) for c in campaigns_summary)
        total_purchases = sum(c.get('purchases', 0) for c in campaigns_summary)
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_cpi = (total_spend / total_installs) if total_installs > 0 else 0
        avg_cpr = (total_spend / total_registrations) if total_registrations > 0 else 0
        avg_cpa = (total_spend / total_purchases) if total_purchases > 0 else 0
        conversion_rate = (total_installs / total_clicks * 100) if total_clicks > 0 else 0

        # Top/Bottom performers
        sorted_by_cpi = sorted([c for c in campaigns_summary if c['installs'] > 0], key=lambda x: x['cpi'])
        best_cpi_campaign = sorted_by_cpi[0] if sorted_by_cpi else None
        worst_cpi_campaign = sorted_by_cpi[-1] if len(sorted_by_cpi) > 1 else None

        sorted_by_ctr = sorted([a for a in ads_summary if a['impressions'] > 0], key=lambda x: x['ctr'], reverse=True)
        best_ctr_ad = sorted_by_ctr[0] if sorted_by_ctr else None
        worst_ctr_ad = sorted_by_ctr[-1] if len(sorted_by_ctr) > 1 else None

        prompt = f"""You are an expert frontend designer and Meta Ads analyst. Generate a STUNNING, comprehensive HTML dashboard.

=== ACCOUNT INFO ===
Account: {account_name}
Date: {date_since}
Generated: {datetime.now().strftime('%b %d, %Y %I:%M %p IST')}
Budget Remaining: {balance.get('balance_formatted', 'N/A')}

=== AGGREGATE METRICS ===
Total Spend: ₹{total_spend:,.2f}
Total Impressions: {total_impressions:,}
Total Clicks: {total_clicks:,}
Average CTR: {avg_ctr:.2f}%

=== CONVERSION FUNNEL ===
Installs: {total_installs} | CPI: ₹{avg_cpi:.2f}
Registrations: {total_registrations} | CPR: ₹{avg_cpr:.2f}
Checkouts: {total_checkouts}
Purchases: {total_purchases} | CPA: ₹{avg_cpa:.2f}
Click-to-Install Rate: {conversion_rate:.2f}%

=== DELTA CHANGES (vs previous period) ===
{json.dumps(deltas, indent=2) if deltas else "First run - no previous data"}

=== TOP PERFORMERS ===
Best CPI Campaign: {best_cpi_campaign['name'] if best_cpi_campaign else 'N/A'} (₹{best_cpi_campaign['cpi'] if best_cpi_campaign else 0})
Worst CPI Campaign: {worst_cpi_campaign['name'] if worst_cpi_campaign else 'N/A'} (₹{worst_cpi_campaign['cpi'] if worst_cpi_campaign else 0})
Best CTR Ad: {best_ctr_ad['name'] if best_ctr_ad else 'N/A'} ({best_ctr_ad['ctr'] if best_ctr_ad else 0}%)
Worst CTR Ad: {worst_ctr_ad['name'] if worst_ctr_ad else 'N/A'} ({worst_ctr_ad['ctr'] if worst_ctr_ad else 0}%)

=== ALL CAMPAIGNS ({len(campaigns_summary)} total) ===
{json.dumps(campaigns_summary, indent=2)}

=== ALL ADSETS ({len(adsets_summary)} total) ===
{json.dumps(adsets_summary, indent=2)}

=== ALL ADS/CREATIVES ({len(ads_summary)} total) ===
{json.dumps(ads_summary, indent=2)}

=== INDUSTRY BENCHMARKS (Education/App Install - India) ===
- Target CPI: ₹50-80
- Good CTR: 1.5-3%
- Excellent CTR: >3%
- Poor CTR: <0.8%
- Good Conversion Rate: 5-10%
- Benchmark CPM: ₹80-150

GENERATE A PREMIUM HTML DASHBOARD WITH THESE SECTIONS:

1. **EXECUTIVE HEADER**
   - Account name with logo placeholder
   - Date range and generation timestamp
   - Budget status with visual indicator (warning if low)
   - Quick health score (0-100) based on overall performance

2. **KPI CARDS ROW** (8-10 cards showing full funnel)
   - Total Spend (with delta)
   - Impressions (with delta)
   - Clicks (with delta)
   - Average CTR (with benchmark)
   - Installs (with delta)
   - Registrations (with delta)
   - Checkouts (with delta)
   - Purchases (with delta)
   - Average CPI (green if below ₹80, red if above)
   - Average CPR (Cost Per Registration)

3. **PERFORMANCE SCORE CARD**
   - Overall score out of 100
   - Breakdown: Efficiency (CPI vs benchmark), Engagement (CTR), Scale (spend utilization)
   - Visual progress bars or gauges

4. **TREND ANALYSIS SECTION**
   - If deltas available: show trend direction for each metric
   - Mini sparkline-style indicators
   - Period-over-period comparison summary

5. **KEY INSIGHTS & ALERTS** (AI-generated, prioritized)
   - 🔴 Critical alerts (high spend + zero conversions, budget running out)
   - 🟡 Warnings (declining performance, high CPI)
   - 🟢 Wins (best performers, improving metrics)
   - 💡 Opportunities (scaling potential, optimization ideas)

6. **PRIORITY ACTION ITEMS**
   - Numbered list of specific actions to take TODAY
   - Each with expected impact (High/Medium/Low)
   - Sorted by urgency

7. **ALL CAMPAIGNS TABLE** (show every campaign)
   - All metrics: Spend, Impressions, Clicks, CTR, Installs, CPI, Registrations, CPR, Checkouts, Purchases, CPA, Status
   - AI columns (Observation, Recommendation, Action, Reason)
   - Color-coded rows based on performance

8. **ALL ADSETS TABLE** (show every adset)
   - Grouped by campaign visually
   - All metrics: Spend, Impressions, Clicks, Installs, CPI, Registrations, CPR, Checkouts, Purchases, Status
   - AI analysis columns

9. **ALL ADS/CREATIVES TABLE** (show every ad)
   - All ads with: Name, AdSet, Campaign, Spend, Impressions, Clicks, CTR, Installs, Registrations, Checkouts, Purchases, Status
   - CTR highlighting (green >2%, red <0.8%)
   - AI recommendations for each ad

10. **BUDGET ANALYSIS SECTION**
    - Spend distribution visualization
    - Budget utilization rate
    - Projected spend at current rate
    - Days until budget exhaustion

11. **COMPETITOR ANALYSIS SECTION** (REAL SCRAPED DATA)
{self._format_competitor_intel(competitor_intel) if competitor_intel else '''
    No live competitor data available. Using general analysis:
    - **SuperKalam** - UPSC preparation app, known for aggressive YouTube ads
    - **CSEwhy** - UPSC coaching with strong video content
    - **Unacademy** - Major player with massive ad spend
'''}

12. **TRENDING TOPICS SECTION** (For Viral Ad Ideas)
    Based on current events and UPSC-relevant topics:
    - Current affairs that can be leveraged for ads
    - Trending memes/formats that can be adapted
    - Seasonal opportunities (exam dates, results, budget, etc.)
    - Content hooks that are performing well
    - Viral ad concepts to test

13. **CREATIVE IDEAS SECTION**
    - 5 specific ad concepts to test this week
    - Hook ideas based on what's working
    - Copy angles to try
    - Visual formats trending on Instagram/Facebook

14. **RECOMMENDATIONS SUMMARY**
    - Top 3 things to SCALE (with expected impact)
    - Top 3 things to PAUSE (with savings estimate)
    - Top 3 things to TEST (with hypothesis)

DESIGN REQUIREMENTS:
- Professional dark theme with blue/black color scheme
- Background: Dark navy/black (#0a0f1a or #0d1117)
- Cards: Dark blue-gray (#151b28 or #1a1f2e) with subtle blue borders
- Accent color: Electric blue (#3b82f6), Cyan (#06b6d4)
- Text: White (#ffffff) for headings, Light gray (#94a3b8) for body
- Success: Green (#10b981), Error: Red (#ef4444), Warning: Amber (#f59e0b)
- Smooth shadows with blue glow
- Rounded corners (12px for cards)
- Inter or system font stack
- Responsive grid layout
- Sticky header with dark gradient

TABLE REQUIREMENTS (CRITICAL):
- Add JavaScript for SORT functionality on all columns (click header to sort)
- Add FILTER input boxes above tables to filter by name/status
- Show ALL rows (not top 10) - display every single ad, adset, campaign
- Table cells must NOT have text cutoff - use:
  - word-wrap: break-word
  - max-width with overflow handling
  - Proper column widths
- Make tables horizontally scrollable on mobile
- Add row hover effects
- Zebra striping for readability

INTERACTIVE FEATURES:
- Clickable column headers for sorting (asc/desc toggle)
- Search/filter box for each table
- Expandable/collapsible sections
- Sticky table headers when scrolling

FORMAT NUMBERS:
- Currency: ₹ symbol with Indian number formatting (lakhs/crores or commas)
- Percentages: 1 decimal place
- Large numbers: with commas

OUTPUT: Return ONLY valid HTML starting with <!DOCTYPE html>. No markdown, no explanations.
"""
        return prompt

    def _format_competitor_intel(self, competitor_intel: Dict) -> str:
        """Format competitor intelligence data for the prompt."""
        if not competitor_intel:
            return ""

        sections = []
        competitors = competitor_intel if isinstance(competitor_intel, list) else [competitor_intel]

        for comp in competitors:
            name = comp.get('competitor', 'Unknown')
            summary = comp.get('summary', {})
            insights = comp.get('insights', {})
            ads = comp.get('ads', [])[:5]  # Top 5 ads

            section = f"""
    **{name}** (LIVE DATA - Scraped {comp.get('scraped_at', 'recently')})
    - Total Active Ads: {summary.get('total_ads', 0)}
    - Media Mix: {summary.get('with_video', 0)} video, {summary.get('with_carousel', 0)} carousel, {summary.get('image_only', 0)} image
    - Primary CTA: {list(summary.get('cta_types', {}).keys())[0] if summary.get('cta_types') else 'Unknown'}
    - Landing Domains: {', '.join(summary.get('landing_domains', {}).keys())[:100]}
    - Avg Days Running: {summary.get('avg_days_running', 0)}
    - New Ads (≤7 days): {summary.get('new_ads_7d', 0)}
    - Evergreen Ads (30+ days): {summary.get('long_running_30d', 0)}

    Strategy Signals:
    {chr(10).join('    - ' + s for s in insights.get('strategy_signals', ['No signals detected']))}

    Messaging Themes: {', '.join(insights.get('messaging_themes', ['Unknown']))}

    Top Ads:"""

            for i, ad in enumerate(ads, 1):
                ad_text = (ad.get('ad_text', '') or '')[:100]
                section += f"""
    {i}. Library ID: {ad.get('library_id', 'N/A')} | Running {ad.get('days_running', '?')} days
       CTA: {ad.get('cta_type', 'Unknown')} | Landing: {ad.get('landing_domain', 'Unknown')}
       Text: "{ad_text}..."
"""
            sections.append(section)

        return "\n".join(sections)

    def _generate_error_dashboard(self, account_name: str, error: str) -> str:
        """Generate a fallback error dashboard when Claude fails."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{account_name} - Dashboard Error</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .error-card {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            max-width: 600px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }}
        h1 {{
            color: #ef4444;
            margin-bottom: 20px;
        }}
        p {{
            color: #666;
            line-height: 1.6;
        }}
        .error-details {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            text-align: left;
            font-family: monospace;
            font-size: 14px;
            color: #991b1b;
        }}
    </style>
</head>
<body>
    <div class="error-card">
        <h1>Dashboard Generation Failed</h1>
        <p>We encountered an error while generating the dashboard for <strong>{account_name}</strong>.</p>
        <p>Please try again or check the logs for more details.</p>
        <div class="error-details">
            Error: {error}
        </div>
        <p style="margin-top: 20px; font-size: 14px; color: #999;">
            Generated: {datetime.now().strftime('%b %d, %Y %I:%M %p IST')}
        </p>
    </div>
</body>
</html>"""
