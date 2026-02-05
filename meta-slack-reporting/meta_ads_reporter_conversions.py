#!/usr/bin/env python3
"""
Meta Ads Slack Reporter - Full conversion tracking with CPI, CPA, etc.
"""

import os
import sys
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

# Load environment variables
load_dotenv()

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
META_ADS_ACCOUNT_ID = os.getenv('META_ADS_ACCOUNT_ID')
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
REPORT_DAYS = int(os.getenv('REPORT_DAYS', 7))
TZ = os.getenv('TZ', 'Asia/Kolkata')
ACCOUNT_NAME = os.getenv('ACCOUNT_NAME', 'Meta Ads')
DETAIL_LEVEL = os.getenv('DETAIL_LEVEL', 'detailed')

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
        return f"₹{amount:,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"


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
    """Return emoji for status"""
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


def extract_actions(insight):
    """Extract conversion actions from insight data"""
    actions = {}

    # Extract action counts
    action_list = insight.get('actions', [])
    for action in action_list:
        action_type = action.get('action_type', '')
        value = int(action.get('value', 0))
        actions[action_type] = value

    # Extract cost per action
    cost_per_action_list = insight.get('cost_per_action_type', [])
    for cpa in cost_per_action_list:
        action_type = cpa.get('action_type', '')
        cost = float(cpa.get('value', 0))
        actions[f"{action_type}_cost"] = cost

    return actions


def fetch_detailed_insights(ad_account, date_range, level='campaign'):
    """Fetch insights with conversion data"""
    try:
        logger.info(f"Fetching {level}-level insights with conversions...")

        params = {
            'time_range': {
                'since': date_range['since'],
                'until': date_range['until']
            },
            'level': level,
            'fields': [
                'campaign_name',
                'campaign_id',
                'adset_name',
                'adset_id',
                'ad_name',
                'ad_id',
                'impressions',
                'reach',
                'spend',
                'clicks',
                'cpc',
                'cpm',
                'ctr',
                'actions',
                'cost_per_action_type',
                'conversions',
                'cost_per_conversion'
            ]
        }

        insights = ad_account.get_insights(params=params)
        insights_data = []

        for insight in insights:
            data = dict(insight)
            # Extract and add conversion actions
            data['parsed_actions'] = extract_actions(data)
            insights_data.append(data)

        logger.info(f"Fetched {len(insights_data)} {level}-level records")
        return insights_data

    except Exception as e:
        logger.error(f"Error fetching {level}-level insights: {e}")
        return []


def aggregate_with_conversions(insights_data, level_key):
    """Aggregate insights including conversion data"""
    aggregated = {}

    for insight in insights_data:
        name = insight.get(level_key, 'Unknown')

        if name not in aggregated:
            aggregated[name] = {
                'spend': 0,
                'impressions': 0,
                'reach': 0,
                'clicks': 0,
                'conversions': {}
            }

        aggregated[name]['spend'] += float(insight.get('spend', 0))
        aggregated[name]['impressions'] += int(insight.get('impressions', 0))
        aggregated[name]['reach'] += int(insight.get('reach', 0))
        aggregated[name]['clicks'] += int(insight.get('clicks', 0))

        # Aggregate conversion actions
        parsed_actions = insight.get('parsed_actions', {})
        for action_type, value in parsed_actions.items():
            if not action_type.endswith('_cost'):
                if action_type not in aggregated[name]['conversions']:
                    aggregated[name]['conversions'][action_type] = 0
                aggregated[name]['conversions'][action_type] += value

    # Calculate cost per action for aggregated data
    for name, data in aggregated.items():
        spend = data['spend']
        conversion_costs = {}
        for action_type, count in data['conversions'].items():
            if count > 0 and not action_type.endswith('_cost'):
                conversion_costs[f"{action_type}_cost"] = spend / count
        data['conversions'].update(conversion_costs)

    # Sort by spend
    return sorted(aggregated.items(), key=lambda x: x[1]['spend'], reverse=True)


def format_conversion_metrics(conversions):
    """Format conversion metrics into readable text"""
    if not conversions:
        return "No conversion data"

    # Priority conversion types to display
    priority_conversions = [
        ('omni_app_install', '📲 App Installs', 'CPI'),
        ('app_install', '📲 App Installs', 'CPI'),
        ('mobile_app_install', '📲 App Installs', 'CPI'),
        ('omni_complete_registration', '✍️ Registrations', 'CPR'),
        ('complete_registration', '✍️ Registrations', 'CPR'),
        ('omni_initiated_checkout', '🛒 Checkouts Started', 'Cost/Checkout'),
        ('initiate_checkout', '🛒 Checkouts Started', 'Cost/Checkout'),
        ('omni_purchase', '💰 Purchases', 'CPA'),
        ('purchase', '💰 Purchases', 'CPA'),
        ('omni_add_to_cart', '🛍️ Add to Cart', 'Cost/Add'),
        ('add_to_cart', '🛍️ Add to Cart', 'Cost/Add'),
        ('omni_view_content', '👁️ Content Views', 'Cost/View'),
        ('view_content', '👁️ Content Views', 'Cost/View'),
        ('link_click', '🔗 Link Clicks', 'Cost/Click'),
        ('landing_page_view', '📄 Landing Page Views', 'Cost/LPV'),
    ]

    lines = []
    for action_type, label, cost_label in priority_conversions:
        count = conversions.get(action_type, 0)
        cost = conversions.get(f"{action_type}_cost", 0)

        if count > 0:
            lines.append(f"   {label}: {int(count):,} ({cost_label}: {format_currency(cost)})")

    return "\n".join(lines) if lines else "No conversions"


def format_comprehensive_report(campaign_data, adset_data, ad_data, date_range, detail_level):
    """Format comprehensive Slack report with conversion data"""
    messages = []

    # Header
    header = (
        f"┌─────────────────────────────────────┐\n"
        f"│  📊 *Meta Ads Performance Report*     │\n"
        f"│  {ACCOUNT_NAME}                        │\n"
        f"│  Last {REPORT_DAYS} Days                        │\n"
        f"│  {date_range['start_date_formatted']} to {date_range['end_date_formatted']}              │\n"
        f"└─────────────────────────────────────┘"
    )

    # Account-level summary with conversions
    if campaign_data:
        total_spend = sum(c[1]['spend'] for c in campaign_data)
        total_impressions = sum(c[1]['impressions'] for c in campaign_data)
        total_reach = sum(c[1]['reach'] for c in campaign_data)
        total_clicks = sum(c[1]['clicks'] for c in campaign_data)
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

        # Aggregate all conversions
        total_conversions = {}
        for _, data in campaign_data:
            for action_type, value in data['conversions'].items():
                if not action_type.endswith('_cost'):
                    if action_type not in total_conversions:
                        total_conversions[action_type] = 0
                    total_conversions[action_type] += value

        # Calculate total cost per action
        for action_type, count in list(total_conversions.items()):
            if count > 0 and not action_type.endswith('_cost'):
                total_conversions[f"{action_type}_cost"] = total_spend / count

        summary = (
            f"\n\n🎯 *Account Summary*\n"
            f"Total Spend: {format_currency(total_spend)}\n"
            f"Total Impressions: {format_number(total_impressions)}\n"
            f"Total Reach: {format_number(total_reach)}\n"
            f"Total Clicks: {format_number(total_clicks)} (CTR: {format_percentage(ctr)})\n"
            f"\n💎 *Total Conversions:*\n"
            f"{format_conversion_metrics(total_conversions)}"
        )

        # Top Campaigns with conversions
        campaigns_text = f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📈 *Top Campaigns (by spend)*\n"
        for idx, (campaign_name, stats) in enumerate(campaign_data[:5], 1):
            ctr_c = (stats['clicks'] / stats['impressions'] * 100) if stats['impressions'] > 0 else 0
            campaigns_text += (
                f"\n{idx}. *{campaign_name[:50]}*\n"
                f"   Spend: {format_currency(stats['spend'])} | "
                f"Imp: {format_number(stats['impressions'])} | "
                f"Clicks: {format_number(stats['clicks'])} ({format_percentage(ctr_c)})\n"
                f"{format_conversion_metrics(stats['conversions'])}\n"
            )

        messages.append({"text": header + summary + campaigns_text})

    # Ad Set Level with conversions
    if detail_level in ['detailed', 'full'] and adset_data:
        adsets_text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📊 *Top Ad Sets (by spend)*\n"
        for idx, (adset_name, stats) in enumerate(adset_data[:8], 1):
            ctr_a = (stats['clicks'] / stats['impressions'] * 100) if stats['impressions'] > 0 else 0
            adsets_text += (
                f"\n{idx}. {adset_name[:45]}\n"
                f"   Spend: {format_currency(stats['spend'])} | "
                f"{format_number(stats['impressions'])} imp | "
                f"{format_number(stats['clicks'])} clicks ({format_percentage(ctr_a)})\n"
                f"{format_conversion_metrics(stats['conversions'])}\n"
            )

        messages.append({"text": adsets_text})

    # Individual Ads with conversions
    if detail_level == 'full' and ad_data:
        ads_text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🎨 *Top Individual Ads (by spend)*\n"
        for idx, (ad_name, stats) in enumerate(ad_data[:8], 1):
            ctr_ad = (stats['clicks'] / stats['impressions'] * 100) if stats['impressions'] > 0 else 0
            ads_text += (
                f"\n{idx}. {ad_name[:40]}\n"
                f"   Spend: {format_currency(stats['spend'])} | "
                f"{format_number(stats['impressions'])} imp | "
                f"{format_number(stats['clicks'])} clicks ({format_percentage(ctr_ad)})\n"
                f"{format_conversion_metrics(stats['conversions'])}\n"
            )

        messages.append({"text": ads_text})

    return messages


def send_to_slack(messages):
    """Send multiple messages to Slack webhook"""
    try:
        success = True
        for message in messages:
            response = requests.post(
                SLACK_WEBHOOK_URL,
                json=message,
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"Failed to send to Slack: {response.status_code} - {response.text}")
                success = False

        if success:
            logger.info(f"Successfully sent {len(messages)} message(s) to Slack")
        return success

    except Exception as e:
        logger.error(f"Error sending to Slack: {e}")
        return False


def main():
    """Main execution flow"""
    logger.info("=" * 60)
    logger.info(f"Starting Meta Ads Reporter with Conversions (Detail Level: {DETAIL_LEVEL})")
    logger.info("=" * 60)

    # Validate environment variables
    if not all([SLACK_WEBHOOK_URL, META_ADS_ACCOUNT_ID, META_ACCESS_TOKEN]):
        logger.error("Missing required environment variables. Check .env file.")
        sys.exit(1)

    # Initialize Facebook API
    try:
        FacebookAdsApi.init(access_token=META_ACCESS_TOKEN)
        logger.info("Facebook API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Facebook API: {e}")
        sys.exit(1)

    # Get date range
    date_range = get_date_range(REPORT_DAYS)
    logger.info(f"Fetching data from {date_range['since']} to {date_range['until']}")

    try:
        ad_account = AdAccount(META_ADS_ACCOUNT_ID)

        # Fetch campaign-level data with conversions
        campaign_insights = fetch_detailed_insights(ad_account, date_range, level='campaign')
        campaign_data = aggregate_with_conversions(campaign_insights, 'campaign_name')

        # Fetch adset-level data
        adset_data = []
        if DETAIL_LEVEL in ['detailed', 'full']:
            adset_insights = fetch_detailed_insights(ad_account, date_range, level='adset')
            adset_data = aggregate_with_conversions(adset_insights, 'adset_name')

        # Fetch ad-level data
        ad_data = []
        if DETAIL_LEVEL == 'full':
            ad_insights = fetch_detailed_insights(ad_account, date_range, level='ad')
            ad_data = aggregate_with_conversions(ad_insights, 'ad_name')

        # Format messages
        messages = format_comprehensive_report(
            campaign_data,
            adset_data,
            ad_data,
            date_range,
            DETAIL_LEVEL
        )

        # Send to Slack
        send_to_slack(messages)

        logger.info("Meta Ads Reporter completed successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        error_message = {
            "text": f"❌ *Meta Ads Reporter Error*\n\n```{str(e)}```"
        }
        send_to_slack([error_message])
        sys.exit(1)


if __name__ == "__main__":
    main()
