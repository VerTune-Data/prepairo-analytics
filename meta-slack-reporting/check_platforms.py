#!/usr/bin/env python3
"""
Check which platforms (Facebook/Instagram) are configured for all campaigns and adsets
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet

# Load environment
import sys

# Always load GRE credentials
env_file = Path(__file__).parent / '.env'
load_dotenv(env_file)

# But allow overriding account ID
if len(sys.argv) > 1 and sys.argv[1] == 'upsc':
    META_ADS_ACCOUNT_ID = 'act_632831043086750'
    print(f"Checking UPSC account: {META_ADS_ACCOUNT_ID}")
else:
    META_ADS_ACCOUNT_ID = os.getenv('META_ADS_ACCOUNT_ID')
    print(f"Checking GRE account: {META_ADS_ACCOUNT_ID}")

META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')

# Initialize API
FacebookAdsApi.init(access_token=META_ACCESS_TOKEN)
ad_account = AdAccount(META_ADS_ACCOUNT_ID)

print("=" * 80)
print("Checking Platform Configuration for All Campaigns & AdSets")
print("=" * 80)
print()

# Fetch all campaigns
campaigns = ad_account.get_campaigns(fields=[
    'id', 'name', 'status', 'effective_status'
])

for campaign in campaigns:
    campaign_id = campaign.get('id')
    campaign_name = campaign.get('name')
    status = campaign.get('effective_status', campaign.get('status'))

    print(f"📊 Campaign: {campaign_name}")
    print(f"   ID: {campaign_id}")
    print(f"   Status: {status}")

    # Get adsets for this campaign
    try:
        adsets = Campaign(campaign_id).get_ad_sets(fields=[
            'id', 'name', 'status', 'effective_status', 'targeting'
        ])

        for adset in adsets:
            adset_name = adset.get('name')
            adset_status = adset.get('effective_status', adset.get('status'))
            targeting = adset.get('targeting', {})

            # Extract platform info from targeting
            publisher_platforms = targeting.get('publisher_platforms', [])
            facebook_positions = targeting.get('facebook_positions', [])
            instagram_positions = targeting.get('instagram_positions', [])

            print(f"   └─ AdSet: {adset_name}")
            print(f"      Status: {adset_status}")

            if publisher_platforms:
                print(f"      Publisher Platforms: {', '.join(publisher_platforms)}")
            else:
                print(f"      Publisher Platforms: Automatic Placements (all platforms)")

            if facebook_positions:
                print(f"      Facebook Positions: {', '.join(facebook_positions)}")
            if instagram_positions:
                print(f"      Instagram Positions: {', '.join(instagram_positions)}")

            # Highlight if Facebook is enabled
            has_facebook = (
                not publisher_platforms or  # Empty means all platforms
                'facebook' in publisher_platforms or
                facebook_positions
            )

            if has_facebook and adset_status == 'ACTIVE':
                print(f"      🔴 FACEBOOK IS ENABLED AND ACTIVE ON THIS ADSET!")
            elif has_facebook:
                print(f"      ⚠️  Facebook is configured (but adset is {adset_status})")

            print()

    except Exception as e:
        print(f"   Error fetching adsets: {e}")

    print()

print("=" * 80)
print("Summary:")
print("If you see 'FACEBOOK IS ENABLED' warnings above, those adsets are still")
print("configured to run on Facebook. You need to edit them in Meta Ads Manager.")
print("=" * 80)
