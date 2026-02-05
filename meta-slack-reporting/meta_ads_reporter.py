#!/usr/bin/env python3
"""
Meta Ads Slack Reporter
Fetches Meta Ads performance data and sends formatted reports to Slack
"""

import os
import sys
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adsinsights import AdsInsights

# Load environment variables
load_dotenv()

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
META_ADS_ACCOUNT_ID = os.getenv('META_ADS_ACCOUNT_ID')
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
REPORT_DAYS = int(os.getenv('REPORT_DAYS', 7))
TZ = os.getenv('TZ', 'Asia/Kolkata')
ACCOUNT_NAME = os.getenv('ACCOUNT_NAME', 'Meta Ads')

# Logging setup
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

today = datetime.now().strftime('%Y%m%d')
log_file = os.path.join(log_dir, f'meta_ads_{today}.log')

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


def initialize_facebook_api():
    """Initialize Facebook Marketing API"""
    try:
        FacebookAdsApi.init(access_token=META_ACCESS_TOKEN)
        logger.info("Facebook API initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Facebook API: {e}")
        return False


def get_date_range(days):
    """Get date range for the report"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return {
        'since': start_date.strftime('%Y-%m-%d'),
        'until': end_date.strftime('%Y-%m-%d'),
        'start_date_formatted': start_date.strftime('%b %d'),
        'end_date_formatted': end_date.strftime('%b %d, %Y')
    }


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
        return []


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
        return []


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


def format_slack_message(aggregated_data, campaigns_data, date_range):
    """Format data into Slack message blocks"""
    if not aggregated_data:
        return {
            "text": "⚠️ No Meta Ads data available for the specified period"
        }

    total = aggregated_data['total']

    # Header
    header = (
        f"┌─────────────────────────────────────┐\n"
        f"│  📊 *Meta Ads Performance Report*     │\n"
        f"│  {ACCOUNT_NAME}                        │\n"
        f"│  Last {REPORT_DAYS} Days                        │\n"
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
    daily_text = f"{separator}\n\n📅 *Daily Breakdown (Last {REPORT_DAYS} Days)*\n"

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


def send_to_slack(message):
    """Send message to Slack webhook"""
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=message,
            timeout=10
        )

        if response.status_code == 200:
            logger.info("Successfully sent report to Slack")
            return True
        else:
            logger.error(f"Failed to send to Slack: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending to Slack: {e}")
        return False


def main():
    """Main execution flow"""
    logger.info("=" * 60)
    logger.info("Starting Meta Ads Reporter")
    logger.info("=" * 60)

    # Validate environment variables
    if not all([SLACK_WEBHOOK_URL, META_ADS_ACCOUNT_ID, META_ACCESS_TOKEN]):
        logger.error("Missing required environment variables. Check .env file.")
        sys.exit(1)

    # Initialize Facebook API
    if not initialize_facebook_api():
        logger.error("Failed to initialize Facebook API. Exiting.")
        sys.exit(1)

    # Get date range
    date_range = get_date_range(REPORT_DAYS)
    logger.info(f"Fetching data from {date_range['since']} to {date_range['until']}")

    try:
        # Initialize Ad Account
        ad_account = AdAccount(META_ADS_ACCOUNT_ID)

        # Fetch campaigns
        campaigns_data = fetch_campaigns(ad_account)

        # Fetch insights
        insights_data = fetch_campaign_insights(ad_account, date_range)

        if not insights_data:
            logger.warning("No insights data available")
            error_message = {
                "text": f"⚠️ No Meta Ads data available for {date_range['start_date_formatted']} to {date_range['end_date_formatted']}"
            }
            send_to_slack(error_message)
            return

        # Aggregate data
        aggregated_data = aggregate_insights(insights_data)

        # Format message
        slack_message = format_slack_message(aggregated_data, campaigns_data, date_range)

        # Send to Slack
        send_to_slack(slack_message)

        logger.info("Meta Ads Reporter completed successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        error_message = {
            "text": f"❌ *Meta Ads Reporter Error*\n\n```{str(e)}```"
        }
        send_to_slack(error_message)
        sys.exit(1)


if __name__ == "__main__":
    main()
