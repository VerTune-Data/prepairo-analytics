#!/usr/bin/env python3
"""
Test Meta Ads API without sending to Slack
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

# Load environment variables
load_dotenv()

META_ADS_ACCOUNT_ID = os.getenv('META_ADS_ACCOUNT_ID')
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_NAME = os.getenv('ACCOUNT_NAME', 'Meta Ads')

print("=" * 60)
print(f"Testing Meta Ads API - {ACCOUNT_NAME}")
print("=" * 60)
print()

# Initialize API
try:
    FacebookAdsApi.init(access_token=META_ACCESS_TOKEN)
    print("✅ API initialized")
except Exception as e:
    print(f"❌ Failed to initialize API: {e}")
    exit(1)

# Get Ad Account
try:
    ad_account = AdAccount(META_ADS_ACCOUNT_ID)
    print(f"✅ Ad Account ID: {META_ADS_ACCOUNT_ID}")
except Exception as e:
    print(f"❌ Failed to get ad account: {e}")
    exit(1)

# Fetch account info
try:
    account_info = ad_account.api_get(fields=['name', 'account_id', 'currency'])
    print(f"✅ Account Name: {account_info.get('name')}")
    print(f"   Currency: {account_info.get('currency')}")
    print()
except Exception as e:
    print(f"❌ Failed to fetch account info: {e}")
    exit(1)

# Fetch campaigns
try:
    print("Fetching campaigns...")
    campaigns = ad_account.get_campaigns(fields=['name', 'status', 'effective_status', 'objective'])

    campaign_list = list(campaigns)
    print(f"✅ Found {len(campaign_list)} campaigns")
    print()

    for idx, campaign in enumerate(campaign_list[:5], 1):  # Show first 5
        print(f"{idx}. {campaign.get('name')}")
        print(f"   Status: {campaign.get('effective_status')}")
        print(f"   Objective: {campaign.get('objective')}")
        print()

except Exception as e:
    print(f"❌ Failed to fetch campaigns: {e}")
    exit(1)

# Fetch insights for last 7 days
try:
    print("Fetching insights (last 7 days)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    params = {
        'time_range': {
            'since': start_date.strftime('%Y-%m-%d'),
            'until': end_date.strftime('%Y-%m-%d')
        },
        'level': 'account',
        'fields': [
            'impressions',
            'reach',
            'spend',
            'clicks',
            'ctr'
        ]
    }

    insights = ad_account.get_insights(params=params)
    insights_list = list(insights)

    if insights_list:
        insight = insights_list[0]
        print("✅ Insights Summary (Last 7 Days):")
        print(f"   Impressions: {insight.get('impressions', 0):,}")
        print(f"   Reach: {insight.get('reach', 0):,}")
        print(f"   Spend: ₹{float(insight.get('spend', 0)):,.2f}")
        print(f"   Clicks: {insight.get('clicks', 0):,}")
        print(f"   CTR: {insight.get('ctr', 0)}%")
        print()
    else:
        print("⚠️  No insights data available for this period")
        print()

except Exception as e:
    print(f"❌ Failed to fetch insights: {e}")
    print()

print("=" * 60)
print("✅ API Test Complete - Ready to generate reports!")
print("=" * 60)
