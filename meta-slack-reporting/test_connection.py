#!/usr/bin/env python3
"""
Quick test script to verify Slack webhook and Meta API credentials
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def test_slack_webhook():
    """Test Slack webhook connection"""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL not found in .env")
        return False

    print(f"📡 Testing Slack webhook...")
    test_message = {
        "text": "✅ *Meta Ads Reporter Test*\n\nSlack webhook is working! Ready for Meta API credentials."
    }

    try:
        response = requests.post(webhook_url, json=test_message, timeout=10)
        if response.status_code == 200:
            print("✅ Slack webhook working! Check your Slack channel.")
            return True
        else:
            print(f"❌ Slack webhook failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing Slack: {e}")
        return False


def test_meta_credentials():
    """Test Meta API credentials"""
    account_id = os.getenv('META_ADS_ACCOUNT_ID')
    access_token = os.getenv('META_ACCESS_TOKEN')

    if not account_id or not access_token:
        print("⚠️  Meta credentials not configured yet")
        return False

    if account_id == 'act_123456789012345' or 'DUMMY' in access_token:
        print("⚠️  Using dummy Meta credentials - replace with real ones")
        return False

    print(f"🔑 Testing Meta API credentials...")

    try:
        from facebook_business.api import FacebookAdsApi
        from facebook_business.adobjects.adaccount import AdAccount

        FacebookAdsApi.init(access_token=access_token)
        ad_account = AdAccount(account_id)

        # Try to fetch account name
        account_info = ad_account.api_get(fields=['name', 'account_id'])
        print(f"✅ Meta API working! Account: {account_info.get('name', 'Unknown')}")
        return True

    except Exception as e:
        print(f"❌ Meta API error: {e}")
        return False


def main():
    print("=" * 60)
    print("Meta Ads Reporter - Connection Test")
    print("=" * 60)
    print()

    slack_ok = test_slack_webhook()
    print()
    meta_ok = test_meta_credentials()
    print()

    print("=" * 60)
    if slack_ok and meta_ok:
        print("✅ All systems ready! Run: python3 meta_ads_reporter.py")
    elif slack_ok:
        print("✅ Slack ready")
        print("⚠️  Waiting for Meta API credentials")
        print()
        print("Next steps:")
        print("1. Get your Meta Ads Account ID (format: act_XXXXXXXXXXXXX)")
        print("2. Generate a long-lived access token")
        print("3. Update .env file")
        print("4. Run this test again")
    else:
        print("❌ Setup incomplete")
    print("=" * 60)


if __name__ == "__main__":
    main()
