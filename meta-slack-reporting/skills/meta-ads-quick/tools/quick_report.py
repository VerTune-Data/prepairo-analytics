#!/usr/bin/env python3
"""
Meta Ads Quick Report Tool
Fast daily performance snapshot without AI overhead
"""

import os
import sys
import logging
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

# Add parent modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.config_loader import load_account_config, ConfigurationError
from modules.error_handler import handle_meta_api_error, handle_slack_error

# Logging setup
LOG_DIR = Path(__file__).parent.parent.parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f'meta_ads_quick_{datetime.now().strftime("%Y%m%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def format_currency(value):
    """Format value as Indian Rupees"""
    try:
        amount = float(value)
        return f"₹{amount:,.0f}"
    except (ValueError, TypeError):
        return "₹0"


def format_number(value):
    """Format large numbers with K/M suffix"""
    try:
        num = float(value)
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"
    except (ValueError, TypeError):
        return "0"


def format_percentage(value):
    """Format as percentage with 2 decimals"""
    try:
        return f"{float(value):.2f}%"
    except (ValueError, TypeError):
        return "0.00%"


def get_status_emoji(status):
    """Return emoji for campaign status"""
    status_map = {
        'ACTIVE': '🟢',
        'PAUSED': '🟡',
        'DELETED': '🔴',
        'ARCHIVED': '⚫',
        'CAMPAIGN_PAUSED': '⏸️',
        'ADSET_PAUSED': '⏸️',
        'DISAPPROVED': '🔴',
        'PENDING_REVIEW': '⏳',
        'IN_PROCESS': '⏳',
    }
    return status_map.get(status, '⚪')


def fetch_campaign_insights(ad_account, date_range):
    """Fetch campaign-level insights from Meta Ads API"""
    try:
        logger.info(f"Fetching insights for account: {ad_account.get_id()}")

        params = {
            'time_range': {
                'since': date_range['since'],
                'until': date_range['until']
            },
            'time_increment': 1,  # Daily breakdown
            'level': 'campaign',
            'fields': [
                'campaign_name',
                'impressions',
                'reach',
                'spend',
                'clicks',
                'cpc',
                'cpm',
                'ctr',
                'actions',
                'date_start'
            ]
        }

        insights = ad_account.get_insights(params=params)

        # Convert to list for processing
        insights_data = []
        for insight in insights:
            insights_data.append(dict(insight))

        logger.info(f"Fetched {len(insights_data)} insight records")
        return insights_data

    except Exception as e:
        logger.error(f"Error fetching campaign insights: {e}")
        raise


def fetch_campaigns(ad_account):
    """Fetch all campaigns with their status"""
    try:
        fields = [
            'name',
            'status',
            'effective_status',
            'objective',
            'daily_budget',
            'lifetime_budget'
        ]

        campaigns = ad_account.get_campaigns(fields=fields)

        campaigns_data = []
        for campaign in campaigns:
            campaigns_data.append(dict(campaign))

        logger.info(f"Fetched {len(campaigns_data)} campaigns")
        return campaigns_data

    except Exception as e:
        logger.error(f"Error fetching campaigns: {e}")
        raise


def aggregate_insights(insights_data):
    """Aggregate insights data for reporting"""
    if not insights_data:
        return None

    # Total metrics
    total_spend = sum(float(i.get('spend', 0)) for i in insights_data)
    total_impressions = sum(int(i.get('impressions', 0)) for i in insights_data)
    total_reach = sum(int(i.get('reach', 0)) for i in insights_data)
    total_clicks = sum(int(i.get('clicks', 0)) for i in insights_data)

    # Calculate CTR
    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

    # Campaign-level aggregation
    campaign_stats = {}
    for insight in insights_data:
        campaign_name = insight.get('campaign_name', 'Unknown')

        if campaign_name not in campaign_stats:
            campaign_stats[campaign_name] = {
                'spend': 0,
                'impressions': 0,
                'reach': 0,
                'clicks': 0
            }

        campaign_stats[campaign_name]['spend'] += float(insight.get('spend', 0))
        campaign_stats[campaign_name]['impressions'] += int(insight.get('impressions', 0))
        campaign_stats[campaign_name]['reach'] += int(insight.get('reach', 0))
        campaign_stats[campaign_name]['clicks'] += int(insight.get('clicks', 0))

    # Sort campaigns by spend
    top_campaigns = sorted(
        campaign_stats.items(),
        key=lambda x: x[1]['spend'],
        reverse=True
    )[:5]  # Top 5 campaigns

    # Daily breakdown
    daily_stats = {}
    for insight in insights_data:
        date = insight.get('date_start', 'Unknown')

        if date not in daily_stats:
            daily_stats[date] = {
                'spend': 0,
                'impressions': 0,
                'clicks': 0
            }

        daily_stats[date]['spend'] += float(insight.get('spend', 0))
        daily_stats[date]['impressions'] += int(insight.get('impressions', 0))
        daily_stats[date]['clicks'] += int(insight.get('clicks', 0))

    # Sort daily stats by date (most recent first)
    daily_breakdown = sorted(
        daily_stats.items(),
        key=lambda x: x[0],
        reverse=True
    )

    return {
        'total': {
            'spend': total_spend,
            'impressions': total_impressions,
            'reach': total_reach,
            'clicks': total_clicks,
            'ctr': ctr
        },
        'top_campaigns': top_campaigns,
        'daily_breakdown': daily_breakdown
    }


def format_slack_message(aggregated_data, campaigns_data, date_range, account_name, report_days):
    """Format data into Slack message blocks"""
    if not aggregated_data:
        return {
            "text": "⚠️ No Meta Ads data available for the specified period"
        }

    total = aggregated_data['total']

    # Header
    header = (
        f"┌─────────────────────────────────────┐\n"
        f"│  📊 *Meta Ads Quick Report*           │\n"
        f"│  {account_name}                        │\n"
        f"│  Last {report_days} Days                        │\n"
        f"│  {date_range['start_date_formatted']} to {date_range['end_date_formatted']}              │\n"
        f"└─────────────────────────────────────┘"
    )

    # Summary section
    summary = (
        f"\n\n🎯 *Campaign Summary*\n"
        f"Total Spend: {format_currency(total['spend'])}\n"
        f"Total Impressions: {format_number(total['impressions'])}\n"
        f"Total Reach: {format_number(total['reach'])}\n"
        f"Total Clicks: {format_number(total['clicks'])} (CTR: {format_percentage(total['ctr'])})"
    )

    # Separator
    separator = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Top campaigns section
    top_campaigns_text = f"{separator}\n\n📈 *Top Campaigns (by spend)*\n"

    # Create campaign name to status map
    campaign_status_map = {c.get('name'): c.get('effective_status', 'UNKNOWN') for c in campaigns_data}

    for idx, (campaign_name, stats) in enumerate(aggregated_data['top_campaigns'], 1):
        status = campaign_status_map.get(campaign_name, 'UNKNOWN')
        emoji = get_status_emoji(status)
        ctr = (stats['clicks'] / stats['impressions'] * 100) if stats['impressions'] > 0 else 0

        top_campaigns_text += (
            f"\n{idx}. *{campaign_name}* [{emoji} {status}]\n"
            f"   Spend: {format_currency(stats['spend'])} | "
            f"Impressions: {format_number(stats['impressions'])}\n"
            f"   Reach: {format_number(stats['reach'])} | "
            f"Clicks: {format_number(stats['clicks'])} ({format_percentage(ctr)})\n"
        )

    # Daily breakdown section
    daily_text = f"{separator}\n\n📅 *Daily Breakdown (Last {min(7, report_days)} Days)*\n"

    for date_str, stats in aggregated_data['daily_breakdown'][:7]:  # Show last 7 days
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%b %d')
        except:
            formatted_date = date_str

        daily_text += (
            f"\n{formatted_date}: {format_currency(stats['spend'])} | "
            f"{format_number(stats['impressions'])} imp | "
            f"{format_number(stats['clicks'])} clicks"
        )

    # Combine all sections
    full_message = header + summary + top_campaigns_text + daily_text

    return {"text": full_message}


def send_to_slack(message, slack_webhook):
    """Send message to Slack webhook"""
    try:
        response = requests.post(
            slack_webhook,
            json=message,
            timeout=10
        )

        if response.status_code == 200:
            logger.info("Successfully sent report to Slack")
            return True
        else:
            error_msg = handle_slack_error(Exception(response.text), response.status_code)
            logger.error(error_msg)
            print(error_msg)
            return False

    except Exception as e:
        error_msg = handle_slack_error(e)
        logger.error(error_msg)
        print(error_msg)
        return False


def main():
    """Main execution flow"""
    parser = argparse.ArgumentParser(description='Meta Ads Quick Report')
    parser.add_argument('--account', type=str, default='gre',
                       choices=['gre', 'upsc', 'test'],
                       help='Account to run report for (default: gre)')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days to include in report (default: 7)')

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info(f"Starting Meta Ads Quick Report for {args.account}")
    logger.info("=" * 60)

    try:
        # Load configuration
        print(f"Loading configuration for {args.account} account...")
        config = load_account_config(args.account)

        # Initialize Facebook API
        print("Connecting to Meta Ads API...")
        FacebookAdsApi.init(access_token=config['access_token'])
        ad_account = AdAccount(config['account_id'])

        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        date_range = {
            'since': start_date.strftime('%Y-%m-%d'),
            'until': end_date.strftime('%Y-%m-%d'),
            'start_date_formatted': start_date.strftime('%b %d'),
            'end_date_formatted': end_date.strftime('%b %d, %Y')
        }

        print(f"Fetching data from {date_range['since']} to {date_range['until']}...")

        # Fetch campaigns
        campaigns_data = fetch_campaigns(ad_account)

        # Fetch insights
        insights_data = fetch_campaign_insights(ad_account, date_range)

        if not insights_data:
            print("⚠️  No insights data available for this period")
            error_message = {
                "text": f"⚠️ No Meta Ads data available for {date_range['start_date_formatted']} to {date_range['end_date_formatted']}"
            }
            send_to_slack(error_message, config['slack_webhook'])
            return

        # Aggregate data
        print("Processing data...")
        aggregated_data = aggregate_insights(insights_data)

        # Format message
        slack_message = format_slack_message(
            aggregated_data,
            campaigns_data,
            date_range,
            config['account_name'],
            args.days
        )

        # Send to Slack
        print("Sending report to Slack...")
        success = send_to_slack(slack_message, config['slack_webhook'])

        if success:
            print("✅ Report sent successfully to Slack")
            logger.info("Meta Ads Quick Report completed successfully")
        else:
            print("❌ Failed to send report to Slack")
            sys.exit(1)

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
            error_message = {
                "text": f"❌ *Meta Ads Quick Report Error*\n\n{error_msg}"
            }
            send_to_slack(error_message, config['slack_webhook'])
        except:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
