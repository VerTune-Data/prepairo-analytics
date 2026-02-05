#!/usr/bin/env python3
"""
Meta Ads {REPORT_INTERVAL_HOURS}-Hour Intelligent Reporting System
Runs every 6 hours with AI-powered insights and historical tracking
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import argparse

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

# Parse command line arguments
parser = argparse.ArgumentParser(description='Meta Ads 8-Hour Intelligent Reporter')
parser.add_argument('--account', type=str, required=True, choices=['upsc', 'gre', 'test'], 
                    help='Account to run report for (upsc, gre, or test)')
args = parser.parse_args()

# Load environment variables for specific account
env_file = Path(__file__).parent / f'.env.{args.account}'
if env_file.exists():
    load_dotenv(env_file)
else:
    print(f"Error: Environment file not found: {env_file}")
    sys.exit(1)

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
REPORT_INTERVAL_HOURS = int(os.getenv('REPORT_INTERVAL_HOURS', '8'))  # Reporting interval in hours
PLATFORMS = os.getenv('PLATFORMS')  # Optional: filter by platforms (e.g., "instagram" or "facebook,instagram")

# Logging setup
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
CHARTS_PATH = Path(__file__).parent / CHARTS_DIR
CHARTS_PATH.mkdir(exist_ok=True)

log_file = LOG_DIR / f'meta_6hour_{datetime.now().strftime("%Y%m%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def get_window_number(hour: int) -> int:
    """
    Determine 8-hour window number
    1 = 03:00-11:00 IST
    2 = 11:00-19:00 IST  
    3 = 19:00-03:00 IST
    """
    if 3 <= hour < 11:
        return 1
    elif 11 <= hour < 19:
        return 2
    else:
        return 3


def main():
    """Main execution flow"""
    logger.info("=" * 80)
    logger.info(f"Starting Meta Ads {REPORT_INTERVAL_HOURS}-Hour Intelligent Reporter for {ACCOUNT_NAME}")
    logger.info("=" * 80)
    
    # Validate environment
    if not all([META_ADS_ACCOUNT_ID, META_ACCESS_TOKEN, SLACK_WEBHOOK_URL]):
        logger.error("Missing required environment variables (META_ADS_ACCOUNT_ID, META_ACCESS_TOKEN, SLACK_WEBHOOK_URL)")
        sys.exit(1)
    
    try:
        # 1. Initialize components
        logger.info("Initializing components...")

        db = MetaAdsDatabase(DB_PATH)
        db.initialize_schema()

        meta_client = MetaAdsAPIClient(META_ADS_ACCOUNT_ID, META_ACCESS_TOKEN, platforms=PLATFORMS)
        slack = SlackFormatter(SLACK_WEBHOOK_URL)
        
        # 2. Fetch Claude API key from AWS Secrets Manager (with fallback)
        claude_api_key = None
        try:
            aws_client = AWSSecretsClient(region=AWS_REGION)
            claude_api_key = aws_client.get_claude_api_key()
            
            if claude_api_key:
                logger.info("Claude API key loaded from AWS Secrets Manager")
            else:
                logger.warning("Claude API key not found in AWS Secrets Manager")
                # Fallback to environment variable
                claude_api_key = os.getenv('CLAUDE_API_KEY')
                if claude_api_key:
                    logger.info("Using Claude API key from environment variable")
        
        except Exception as e:
            logger.warning(f"AWS Secrets Manager error: {e}. Trying environment variable...")
            claude_api_key = os.getenv('CLAUDE_API_KEY')
            if claude_api_key:
                logger.info("Using Claude API key from environment variable")
        
        # 3. Fetch YESTERDAY's complete data (IST-based)
        now = datetime.now()
        window_number = get_window_number(now.hour)

        logger.info(f"Fetching YESTERDAY's data (full day, IST)")

        campaigns = meta_client.fetch_yesterday_insights(level='campaign')
        adsets = meta_client.fetch_yesterday_insights(level='adset')
        ads = meta_client.fetch_yesterday_insights(level='ad')
        balance = meta_client.fetch_account_balance()

        # Get yesterday's date for snapshot
        from datetime import timedelta
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        yesterday = (datetime.now(ist) - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetched {len(campaigns)} campaigns, {len(adsets)} adsets, {len(ads)} ads")

        # 4. Save snapshot
        snapshot_data = {
            'account_id': META_ADS_ACCOUNT_ID,
            'snapshot_time': now,
            'date_since': yesterday,
            'window_number': window_number,
            'campaigns': campaigns,
            'adsets': adsets,
            'ads': ads,
            'balance': balance
        }
        
        snapshot_id = db.save_snapshot(META_ADS_ACCOUNT_ID, snapshot_data)
        logger.info(f"Saved snapshot {snapshot_id}")
        
        # Save denormalized metrics
        if campaigns:
            db.save_campaign_metrics(snapshot_id, campaigns)
        if adsets:
            db.save_adset_metrics(snapshot_id, adsets)
        if ads:
            db.save_ad_metrics(snapshot_id, ads)
        
        # 5. Get previous snapshot and calculate deltas
        previous = db.get_previous_snapshot(META_ADS_ACCOUNT_ID, now, hours_ago=REPORT_INTERVAL_HOURS)
        
        if not previous:
            logger.info("No previous snapshot found - this is the first run")
            
            # Generate current window AI analysis (no trends since no previous data)
            current_analysis = ""
            if claude_api_key:
                try:
                    claude = ClaudeAnalyzer(claude_api_key, model=CLAUDE_MODEL)
                    current_analysis, _ = claude.analyze_6hour_window(snapshot_data, None, ACCOUNT_NAME)
                    logger.info("Generated AI analysis for first run")
                except Exception as e:
                    logger.error(f"Claude analysis failed on first run: {e}")
                    current_analysis = "⚠️ AI analysis unavailable"
            else:
                current_analysis = "⚠️ AI analysis disabled (no API key)"
            
            # Generate charts
            chart_gen = ChartGenerator()
            campaign_data = [{'name': c.get('campaign_name', 'Unknown'), 'spend': float(c.get('spend', 0))} 
                           for c in snapshot_data.get('campaigns', [])]
            emoji_chart = chart_gen.generate_emoji_chart(campaign_data[:10], 'spend')
            
            # Generate PNG charts for first run
            campaigns_for_chart = snapshot_data.get('campaigns', [])

            traffic_png_path = CHARTS_PATH / f'traffic_{snapshot_id}.png'
            conversion_png_path = CHARTS_PATH / f'conversions_{snapshot_id}.png'

            traffic_url = None
            conversion_url = None

            if campaigns_for_chart:
                # Generate traffic chart
                chart_gen.generate_traffic_chart(
                    campaigns_for_chart,
                    f'{ACCOUNT_NAME} - Traffic Metrics (Yesterday)',
                    str(traffic_png_path)
                )

                # Generate conversion chart
                chart_gen.generate_conversion_chart(
                    campaigns_for_chart,
                    f'{ACCOUNT_NAME} - Conversion Metrics (Yesterday)',
                    str(conversion_png_path)
                )
                
                # Upload to S3
                logger.info("Uploading first run charts to S3...")
                s3_uploader = S3ChartUploader(bucket_name=S3_BUCKET, region=AWS_REGION)
                s3_uploader.ensure_bucket_exists()

                traffic_url = s3_uploader.upload_chart(str(traffic_png_path))
                conversion_url = s3_uploader.upload_chart(str(conversion_png_path))

                if traffic_url:
                    logger.info(f"Traffic chart uploaded to S3: {traffic_url}")
                if conversion_url:
                    logger.info(f"Conversion chart uploaded to S3: {conversion_url}")

            charts = {
                'emoji_chart': emoji_chart,
                'traffic_url': traffic_url,
                'conversion_url': conversion_url
            }
            
            slack.send_first_run_message(snapshot_data, current_analysis, charts, ACCOUNT_NAME)
            db.cleanup_old_snapshots(days_to_keep=30)
            db.close()
            return
        
        logger.info(f"Found previous snapshot from {previous.get('snapshot_time')}")
        
        delta_calc = DeltaCalculator()
        deltas = delta_calc.calculate_deltas(snapshot_data, previous)
        
        # 6. Generate Claude analysis (if API key available)
        claude_insights = ""
        if claude_api_key:
            try:
                claude = ClaudeAnalyzer(claude_api_key, model=CLAUDE_MODEL)
                claude_insights = claude.analyze_6hour_window(snapshot_data, previous, ACCOUNT_NAME)
                
                # Save analysis to database
                db.save_claude_analysis(
                    snapshot_id,
                    previous.get('id'),
                    claude.last_prompt,
                    claude_insights,
                    CLAUDE_MODEL
                )
            except Exception as e:
                logger.error(f"Claude analysis failed: {e}")
                claude_insights = f"⚠️ AI analysis unavailable: {str(e)}"
        else:
            logger.warning("Skipping Claude analysis - no API key available")
            claude_insights = "⚠️ AI analysis disabled (no API key)"
        
        # 7. Generate charts
        logger.info("Generating charts...")
        chart_gen = ChartGenerator()

        campaign_deltas = deltas.get('campaigns', [])
        emoji_chart = chart_gen.generate_emoji_chart(campaign_deltas[:10], 'spend')

        # Generate both traffic and conversion charts with raw campaign data
        traffic_png_path = CHARTS_PATH / f'traffic_{snapshot_id}.png'
        conversion_png_path = CHARTS_PATH / f'conversions_{snapshot_id}.png'

        chart_gen.generate_traffic_chart(
            campaigns,
            f'{ACCOUNT_NAME} - Traffic Metrics (Yesterday)',
            str(traffic_png_path)
        )

        chart_gen.generate_conversion_chart(
            campaigns,
            f'{ACCOUNT_NAME} - Conversion Metrics (Yesterday)',
            str(conversion_png_path)
        )

        # Upload to S3
        logger.info("Uploading charts to S3...")
        s3_uploader = S3ChartUploader(bucket_name=S3_BUCKET, region=AWS_REGION)
        s3_uploader.ensure_bucket_exists()

        traffic_url = s3_uploader.upload_chart(str(traffic_png_path))
        conversion_url = s3_uploader.upload_chart(str(conversion_png_path))

        if traffic_url:
            logger.info(f"Traffic chart uploaded to S3: {traffic_url}")
        if conversion_url:
            logger.info(f"Conversion chart uploaded to S3: {conversion_url}")

        if not traffic_url and not conversion_url:
            logger.warning("Failed to upload charts to S3, will skip images in Slack")

        # 8. Format and send to Slack
        logger.info("Formatting and sending Slack report...")

        charts = {
            'emoji_chart': emoji_chart,
            'traffic_url': traffic_url if traffic_url else None,
            'conversion_url': conversion_url if conversion_url else None
        }
        
        messages = slack.format_6hour_report(
            snapshot_data,
            deltas,
            claude_insights,
            charts,
            ACCOUNT_NAME,
            interval_hours=REPORT_INTERVAL_HOURS
        )
        
        success = slack.send_to_slack(messages)
        
        if success:
            logger.info("✅ Report sent successfully to Slack")
        else:
            logger.error("❌ Failed to send report to Slack")
        
        # 9. Cleanup old data
        deleted = db.cleanup_old_snapshots(days_to_keep=30)
        logger.info(f"Cleaned up {deleted} old snapshots")
        
        # 10. Close database
        db.close()
        
        logger.info("=" * 80)
        logger.info(f"Meta Ads {REPORT_INTERVAL_HOURS}-Hour Intelligent Reporter completed successfully")
        logger.info("=" * 80)
    
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        
        # Send error to Slack
        try:
            slack = SlackFormatter(SLACK_WEBHOOK_URL)
            slack.send_error_message(str(e), ACCOUNT_NAME)
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()
