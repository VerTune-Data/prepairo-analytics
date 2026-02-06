#!/usr/bin/env python3
"""
Daily Meta Ads Report with Competitor Intelligence
Runs at 12 PM daily, generates dashboard with competitor analysis and sends to Slack

Usage:
    python daily_report_with_competitors.py --account upsc
    python daily_report_with_competitors.py --account upsc --test  # Send to test channel
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.database import MetaAdsDatabase
from modules.meta_api import MetaAdsAPIClient
from modules.aws_secrets import AWSSecretsClient
from modules.claude_analyzer import ClaudeAnalyzer
from modules.chart_generator import ChartGenerator
from modules.slack_formatter import SlackFormatter
from modules.delta_calculator import DeltaCalculator
from modules.s3_uploader import S3ChartUploader
from modules.dashboard_generator import DashboardGenerator

# Import competitor scraper
from competitor_intel_scraper import CompetitorIntelScraper, COMPETITORS

# Parse arguments
parser = argparse.ArgumentParser(description='Daily Meta Ads Report with Competitor Intelligence')
parser.add_argument('--account', type=str, required=True, choices=['upsc', 'gre', 'test'],
                    help='Account to run report for')
parser.add_argument('--test', action='store_true',
                    help='Send to test Slack channel instead of production')
parser.add_argument('--skip-competitors', action='store_true',
                    help='Skip competitor scraping (faster for testing)')
args = parser.parse_args()

# Load environment - load account config first, then override Slack if test mode
env_file = Path(__file__).parent / f'.env.{args.account}'
if env_file.exists():
    load_dotenv(env_file)
else:
    print(f"Error: Environment file not found: {env_file}")
    sys.exit(1)

# If test mode, override Slack webhook with test channel
if args.test:
    test_env_file = Path(__file__).parent / '.env.test'
    if test_env_file.exists():
        from dotenv import dotenv_values
        test_config = dotenv_values(test_env_file)
        os.environ['SLACK_WEBHOOK_URL'] = test_config.get('SLACK_WEBHOOK_URL', os.getenv('SLACK_WEBHOOK_URL'))

# Configuration
META_ADS_ACCOUNT_ID = os.getenv('META_ADS_ACCOUNT_ID')
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
ACCOUNT_NAME = os.getenv('ACCOUNT_NAME', 'Meta Ads')
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')
DB_PATH = os.getenv('DB_PATH', 'meta_ads_history.db')
CHARTS_DIR = os.getenv('CHARTS_DIR', 'charts')
S3_BUCKET = os.getenv('S3_BUCKET', 'prepairo-analytics-reports')
PLATFORMS = os.getenv('PLATFORMS')

# Logging setup
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
CHARTS_PATH = Path(__file__).parent / CHARTS_DIR
CHARTS_PATH.mkdir(exist_ok=True)
COMPETITOR_DIR = Path(__file__).parent / 'competitor_intel'
COMPETITOR_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / f'daily_report_{datetime.now().strftime("%Y%m%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def scrape_competitors() -> list:
    """Scrape competitor ad intelligence."""
    logger.info("Starting competitor intelligence scraping...")

    # Competitors to scrape (focused on UPSC)
    competitors_to_scrape = ['superkalam', 'csewhy', 'prepairo']

    scraper = CompetitorIntelScraper(headless=True)
    results = []

    try:
        await scraper.start()

        for comp_key in competitors_to_scrape:
            try:
                logger.info(f"Scraping {comp_key}...")
                result = await scraper.scrape_competitor(comp_key)
                results.append(result)

                # Save individual result
                output_file = COMPETITOR_DIR / f"{comp_key}_latest.json"
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)

                await asyncio.sleep(2)  # Be nice to Facebook

            except Exception as e:
                logger.error(f"Error scraping {comp_key}: {e}")
                continue

    finally:
        await scraper.stop()

    # Save combined results
    combined_file = COMPETITOR_DIR / f"all_competitors_{datetime.now().strftime('%Y%m%d')}.json"
    with open(combined_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Competitor scraping complete. {len(results)} competitors scraped.")
    return results


def run_meta_ads_report(competitor_intel: list = None):
    """Run the Meta Ads report with competitor intelligence."""
    logger.info("=" * 80)
    logger.info(f"Starting Daily Meta Ads Report for {ACCOUNT_NAME}")
    if args.test:
        logger.info("*** TEST MODE - Sending to test Slack channel ***")
    logger.info("=" * 80)

    # Validate environment
    if not all([META_ADS_ACCOUNT_ID, META_ACCESS_TOKEN, SLACK_WEBHOOK_URL]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    try:
        # Initialize AWS Secrets
        secrets_client = AWSSecretsClient(region=AWS_REGION)
        anthropic_key = secrets_client.get_claude_api_key()
        if not anthropic_key:
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')

        # Initialize components
        logger.info("Initializing components...")
        db = MetaAdsDatabase(DB_PATH)
        meta_client = MetaAdsAPIClient(META_ADS_ACCOUNT_ID, META_ACCESS_TOKEN, platforms=PLATFORMS)
        slack_formatter = SlackFormatter(SLACK_WEBHOOK_URL)
        delta_calculator = DeltaCalculator()
        chart_generator = ChartGenerator()
        s3_uploader = S3ChartUploader(S3_BUCKET, AWS_REGION)
        dashboard_generator = DashboardGenerator(anthropic_key, CLAUDE_MODEL)

        # Fetch Meta Ads data
        logger.info("Fetching Meta Ads data...")

        # Get yesterday's data for daily report
        campaigns = meta_client.fetch_yesterday_insights('campaign')
        adsets = meta_client.fetch_yesterday_insights('adset')
        ads = meta_client.fetch_yesterday_insights('ad')

        # Get account balance
        try:
            balance = meta_client.get_account_balance()
        except Exception as e:
            logger.warning(f"Could not fetch account balance: {e}")
            balance = {}

        # Calculate totals
        total_spend = sum(float(c.get('spend', 0)) for c in campaigns)
        total_impressions = sum(int(c.get('impressions', 0)) for c in campaigns)
        total_clicks = sum(int(c.get('clicks', 0)) for c in campaigns)

        logger.info(f"Fetched: {len(campaigns)} campaigns, {len(adsets)} adsets, {len(ads)} ads")
        logger.info(f"Totals: Spend ₹{total_spend:.2f}, Impressions {total_impressions}, Clicks {total_clicks}")

        # Prepare snapshot data
        now = datetime.now()
        snapshot_data = {
            'campaigns': campaigns,
            'adsets': adsets,
            'ads': ads,
            'balance': balance,
            'date_since': now.strftime('%Y-%m-%d'),
            'snapshot_time': now.isoformat(),
            'window_number': 1  # Daily report window
        }

        # Get previous snapshot for delta calculation
        previous_snapshot = db.get_latest_snapshot(META_ADS_ACCOUNT_ID)
        deltas = {}
        if previous_snapshot:
            deltas = delta_calculator.calculate_deltas(snapshot_data, previous_snapshot)
            logger.info(f"Delta calculation complete: {len(deltas)} changes detected")

        # Save current snapshot
        db.save_snapshot(META_ADS_ACCOUNT_ID, snapshot_data)

        # Generate HTML Dashboard with competitor intel
        logger.info("Generating HTML dashboard with competitor intelligence...")
        html_dashboard = dashboard_generator.generate_dashboard(
            snapshot_data,
            deltas,
            ACCOUNT_NAME,
            competitor_intel=competitor_intel  # Include competitor data
        )

        # Save dashboard locally
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dashboard_filename = f'daily_report_{timestamp}.html'
        dashboard_path = CHARTS_PATH / dashboard_filename
        with open(dashboard_path, 'w') as f:
            f.write(html_dashboard)
        logger.info(f"Dashboard saved: {dashboard_path}")

        # Upload to S3
        logger.info("Uploading dashboard to S3...")
        dashboard_url = s3_uploader.upload_html(str(dashboard_path), f'meta-ads-charts/{dashboard_filename}')
        logger.info(f"Dashboard URL: {dashboard_url}")

        # Generate charts (optional - main value is in dashboard)
        logger.info("Generating performance charts...")
        chart_urls = []
        try:
            # Generate traffic chart
            traffic_chart_path = str(CHARTS_PATH / f'traffic_{timestamp}.png')
            chart_generator.generate_traffic_chart(campaigns, f"{ACCOUNT_NAME} Traffic", traffic_chart_path)
            chart_url = s3_uploader.upload_chart(traffic_chart_path)
            if chart_url:
                chart_urls.append(chart_url)
        except Exception as e:
            logger.warning(f"Chart generation skipped: {e}")

        # Send to Slack
        logger.info("Sending to Slack...")

        # Main message with dashboard link
        main_message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 {ACCOUNT_NAME} - Daily Report",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Date:* {datetime.now().strftime('%b %d, %Y')}\n*Report Type:* Daily + Competitor Intelligence"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Total Spend:*\n₹{total_spend:,.2f}"},
                        {"type": "mrkdwn", "text": f"*Impressions:*\n{total_impressions:,}"},
                        {"type": "mrkdwn", "text": f"*Clicks:*\n{total_clicks:,}"},
                        {"type": "mrkdwn", "text": f"*Campaigns:*\n{len(campaigns)}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📈 *<{dashboard_url}|View Full Dashboard>* (with competitor analysis)"
                    }
                }
            ]
        }

        # Add competitor summary
        if competitor_intel:
            comp_summary = "\n".join([
                f"• *{c.get('competitor', 'Unknown')}*: {c.get('summary', {}).get('total_ads', 0)} active ads"
                for c in competitor_intel
            ])
            main_message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔍 Competitor Intel:*\n{comp_summary}"
                }
            })

        # Send main message
        response = requests.post(SLACK_WEBHOOK_URL, json=main_message)
        if response.status_code != 200:
            logger.error(f"Slack error: {response.text}")
        else:
            logger.info("Slack message sent successfully!")

        logger.info("=" * 80)
        logger.info("Daily report complete!")
        logger.info(f"Dashboard: {dashboard_url}")
        logger.info("=" * 80)

        return dashboard_url

    except Exception as e:
        logger.error(f"Error in daily report: {e}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Main execution flow."""
    try:
        # Step 1: Scrape competitors (unless skipped)
        competitor_intel = None
        if not args.skip_competitors:
            competitor_intel = await scrape_competitors()
        else:
            # Try to load cached competitor data
            cached_file = COMPETITOR_DIR / 'all_competitors_latest.json'
            if cached_file.exists():
                with open(cached_file) as f:
                    competitor_intel = json.load(f)
                logger.info("Using cached competitor data")

        # Step 2: Run Meta Ads report with competitor intel
        dashboard_url = run_meta_ads_report(competitor_intel)

        return dashboard_url

    except Exception as e:
        logger.error(f"Daily report failed: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())
