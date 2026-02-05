#!/usr/bin/env python3
"""
Meta Ads Analyze Tool
Deep AI-powered analysis with trends and conversions
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# Add parent modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.config_loader import load_account_config, ConfigurationError
from modules.error_handler import handle_meta_api_error, handle_aws_error
from modules.database import MetaAdsDatabase
from modules.meta_api import MetaAdsAPIClient
from modules.aws_secrets import AWSSecretsClient
from modules.claude_analyzer import ClaudeAnalyzer
from modules.chart_generator import ChartGenerator
from modules.slack_formatter import SlackFormatter
from modules.delta_calculator import DeltaCalculator
from modules.s3_uploader import S3ChartUploader

# Logging setup
LOG_DIR = Path(__file__).parent.parent.parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f'meta_ads_analyze_{datetime.now().strftime("%Y%m%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main execution flow"""
    parser = argparse.ArgumentParser(description='Meta Ads Deep Analysis')
    parser.add_argument('--account', type=str, default='gre',
                       choices=['gre', 'upsc', 'test'],
                       help='Account to run report for (default: gre)')
    parser.add_argument('--range', type=str, default='yesterday',
                       choices=['yesterday', '7d', '30d'],
                       help='Time range for analysis (default: yesterday)')
    parser.add_argument('--ai', type=str, default='on',
                       choices=['on', 'off'],
                       help='Enable/disable AI analysis (default: on)')
    parser.add_argument('--charts', type=str, default='on',
                       choices=['on', 'off'],
                       help='Enable/disable chart generation (default: on)')

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info(f"Starting Meta Ads Deep Analysis for {args.account}")
    logger.info("=" * 80)

    try:
        # Load configuration
        print(f"Loading configuration for {args.account} account...")
        config = load_account_config(args.account)

        # Initialize components
        print("Initializing components...")
        db = MetaAdsDatabase(config['db_path'])
        db.initialize_schema()

        meta_client = MetaAdsAPIClient(
            config['account_id'],
            config['access_token'],
            platforms=config['platforms']
        )
        slack = SlackFormatter(config['slack_webhook'])

        # Create charts directory
        charts_dir = Path(__file__).parent.parent.parent.parent / config['charts_dir']
        charts_dir.mkdir(exist_ok=True)

        # Fetch Claude API key if AI is enabled
        claude_api_key = None
        if args.ai == 'on':
            try:
                print("Loading Claude API key from AWS Secrets Manager...")
                aws_client = AWSSecretsClient(region=config['aws_region'])
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

        # Fetch yesterday's complete data (IST-based)
        print(f"Fetching data for {args.range}...")
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        yesterday_ist = now_ist - timedelta(days=1)
        yesterday_date = yesterday_ist.strftime('%Y-%m-%d')

        logger.info(f"Fetching YESTERDAY's data ({yesterday_date} IST)")

        campaigns = meta_client.fetch_yesterday_insights(level='campaign')
        adsets = meta_client.fetch_yesterday_insights(level='adset')
        ads = meta_client.fetch_yesterday_insights(level='ad')
        balance = meta_client.fetch_account_balance()

        logger.info(f"Fetched {len(campaigns)} campaigns, {len(adsets)} adsets, {len(ads)} ads")

        # Save snapshot
        now = datetime.now()
        snapshot_data = {
            'account_id': config['account_id'],
            'snapshot_time': now,
            'date_since': yesterday_date,
            'window_number': 1,
            'campaigns': campaigns,
            'adsets': adsets,
            'ads': ads,
            'balance': balance
        }

        snapshot_id = db.save_snapshot(config['account_id'], snapshot_data)
        logger.info(f"Saved snapshot {snapshot_id}")

        # Save denormalized metrics
        if campaigns:
            db.save_campaign_metrics(snapshot_id, campaigns)
        if adsets:
            db.save_adset_metrics(snapshot_id, adsets)
        if ads:
            db.save_ad_metrics(snapshot_id, ads)

        # Get previous snapshot and calculate deltas
        previous = db.get_previous_snapshot(config['account_id'], now, hours_ago=24)

        if not previous:
            logger.info("No previous snapshot found - this is the first run")
            print("⚠️  This is the first run - no historical comparison available")

            # Generate current window AI analysis (no trends since no previous data)
            current_analysis = ""
            if claude_api_key and args.ai == 'on':
                try:
                    print("Generating AI analysis...")
                    claude = ClaudeAnalyzer(claude_api_key, model=config['claude_model'])
                    current_analysis, _ = claude.analyze_6hour_window(
                        snapshot_data,
                        None,
                        config['account_name']
                    )
                    logger.info("Generated AI analysis for first run")
                except Exception as e:
                    logger.error(f"Claude analysis failed on first run: {e}")
                    current_analysis = "⚠️ AI analysis unavailable"
            else:
                current_analysis = "⚠️ AI analysis disabled"

            # Generate charts if enabled
            traffic_url = None
            conversion_url = None

            if args.charts == 'on' and campaigns:
                try:
                    print("Generating charts...")
                    chart_gen = ChartGenerator()

                    traffic_png_path = charts_dir / f'traffic_{snapshot_id}.png'
                    conversion_png_path = charts_dir / f'conversions_{snapshot_id}.png'

                    chart_gen.generate_traffic_chart(
                        campaigns,
                        f'{config["account_name"]} - Traffic Metrics (Yesterday)',
                        str(traffic_png_path)
                    )

                    chart_gen.generate_conversion_chart(
                        campaigns,
                        f'{config["account_name"]} - Conversion Metrics (Yesterday)',
                        str(conversion_png_path)
                    )

                    # Upload to S3
                    print("Uploading charts to S3...")
                    s3_uploader = S3ChartUploader(
                        bucket_name=config['s3_bucket'],
                        region=config['aws_region']
                    )
                    s3_uploader.ensure_bucket_exists()

                    traffic_url = s3_uploader.upload_chart(str(traffic_png_path))
                    conversion_url = s3_uploader.upload_chart(str(conversion_png_path))

                    if traffic_url:
                        logger.info(f"Traffic chart uploaded to S3: {traffic_url}")
                    if conversion_url:
                        logger.info(f"Conversion chart uploaded to S3: {conversion_url}")

                except Exception as e:
                    logger.warning(f"Chart generation/upload failed: {e}")
                    print(f"⚠️  Chart generation failed: {e}")

            # Emoji chart
            chart_gen = ChartGenerator()
            campaign_data = [{'name': c.get('campaign_name', 'Unknown'), 'spend': float(c.get('spend', 0))}
                           for c in campaigns]
            emoji_chart = chart_gen.generate_emoji_chart(campaign_data[:10], 'spend')

            charts = {
                'emoji_chart': emoji_chart,
                'traffic_url': traffic_url,
                'conversion_url': conversion_url
            }

            print("Sending report to Slack...")
            slack.send_first_run_message(snapshot_data, current_analysis, charts, config['account_name'])

            print("✅ Analysis complete - report sent to Slack")
            logger.info("First run completed successfully")

            db.cleanup_old_snapshots(days_to_keep=30)
            db.close()
            return

        logger.info(f"Found previous snapshot from {previous.get('snapshot_time')}")
        print("Calculating trends vs previous period...")

        delta_calc = DeltaCalculator()
        deltas = delta_calc.calculate_deltas(snapshot_data, previous)

        # Generate Claude analysis (if API key available and enabled)
        claude_insights = ""
        if claude_api_key and args.ai == 'on':
            try:
                print("Generating AI analysis...")
                claude = ClaudeAnalyzer(claude_api_key, model=config['claude_model'])
                claude_insights = claude.analyze_6hour_window(
                    snapshot_data,
                    previous,
                    config['account_name']
                )

                # Save analysis to database
                db.save_claude_analysis(
                    snapshot_id,
                    previous.get('id'),
                    claude.last_prompt,
                    claude_insights,
                    config['claude_model']
                )
            except Exception as e:
                logger.error(f"Claude analysis failed: {e}")
                claude_insights = f"⚠️ AI analysis unavailable: {str(e)}"
        else:
            logger.warning("Skipping Claude analysis")
            claude_insights = "⚠️ AI analysis disabled"

        # Generate charts if enabled
        traffic_url = None
        conversion_url = None

        if args.charts == 'on' and campaigns:
            try:
                print("Generating charts...")
                chart_gen = ChartGenerator()

                traffic_png_path = charts_dir / f'traffic_{snapshot_id}.png'
                conversion_png_path = charts_dir / f'conversions_{snapshot_id}.png'

                chart_gen.generate_traffic_chart(
                    campaigns,
                    f'{config["account_name"]} - Traffic Metrics (Yesterday)',
                    str(traffic_png_path)
                )

                chart_gen.generate_conversion_chart(
                    campaigns,
                    f'{config["account_name"]} - Conversion Metrics (Yesterday)',
                    str(conversion_png_path)
                )

                # Upload to S3
                print("Uploading charts to S3...")
                s3_uploader = S3ChartUploader(
                    bucket_name=config['s3_bucket'],
                    region=config['aws_region']
                )
                s3_uploader.ensure_bucket_exists()

                traffic_url = s3_uploader.upload_chart(str(traffic_png_path))
                conversion_url = s3_uploader.upload_chart(str(conversion_png_path))

                if traffic_url:
                    logger.info(f"Traffic chart uploaded to S3: {traffic_url}")
                if conversion_url:
                    logger.info(f"Conversion chart uploaded to S3: {conversion_url}")

            except Exception as e:
                logger.warning(f"Chart generation/upload failed: {e}")
                print(f"⚠️  Chart generation failed: {e}")

        # Emoji chart
        chart_gen = ChartGenerator()
        campaign_deltas = deltas.get('campaigns', [])
        emoji_chart = chart_gen.generate_emoji_chart(campaign_deltas[:10], 'spend')

        charts = {
            'emoji_chart': emoji_chart,
            'traffic_url': traffic_url,
            'conversion_url': conversion_url
        }

        # Format and send to Slack
        print("Sending report to Slack...")
        messages = slack.format_6hour_report(
            snapshot_data,
            deltas,
            claude_insights,
            charts,
            config['account_name'],
            interval_hours=24
        )

        success = slack.send_to_slack(messages)

        if success:
            print("✅ Analysis complete - report sent to Slack")
            logger.info("Analysis completed successfully")
        else:
            print("❌ Failed to send report to Slack")
            logger.error("Failed to send report to Slack")

        # Cleanup old data
        deleted = db.cleanup_old_snapshots(days_to_keep=30)
        logger.info(f"Cleaned up {deleted} old snapshots")

        # Close database
        db.close()

    except ConfigurationError as e:
        print(str(e))
        logger.error(str(e))
        sys.exit(1)

    except Exception as e:
        error_msg = handle_meta_api_error(e)
        print(error_msg)
        logger.error(f"Error in main execution: {e}", exc_info=True)

        # Try to send error to Slack
        try:
            config = load_account_config(args.account)
            slack = SlackFormatter(config['slack_webhook'])
            slack.send_error_message(str(e), config['account_name'])
        except:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
