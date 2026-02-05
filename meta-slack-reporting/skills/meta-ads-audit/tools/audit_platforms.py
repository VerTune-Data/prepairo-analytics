#!/usr/bin/env python3
"""
Meta Ads Platform Audit Tool
Check which platforms (Facebook/Instagram) are configured for campaigns and adsets
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign

# Add parent modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.config_loader import load_account_config, ConfigurationError
from modules.error_handler import handle_meta_api_error

# Logging setup
LOG_DIR = Path(__file__).parent.parent.parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f'meta_ads_audit_{datetime.now().strftime("%Y%m%d")}.log' if 'datetime' in dir() else LOG_DIR / 'meta_ads_audit.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def audit_platforms(ad_account, account_name):
    """Audit platform configuration for all campaigns and adsets"""
    print("=" * 80)
    print(f"Platform Configuration Audit: {account_name}")
    print("=" * 80)
    print()

    # Fetch all campaigns
    campaigns = ad_account.get_campaigns(fields=[
        'id', 'name', 'status', 'effective_status'
    ])

    facebook_active_count = 0
    facebook_paused_count = 0
    instagram_only_count = 0
    automatic_count = 0

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

                    # Check if Instagram-only
                    if publisher_platforms == ['instagram']:
                        instagram_only_count += 1
                else:
                    print(f"      Publisher Platforms: Automatic Placements (all platforms)")
                    automatic_count += 1

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
                    facebook_active_count += 1
                elif has_facebook:
                    print(f"      ⚠️  Facebook is configured (but adset is {adset_status})")
                    facebook_paused_count += 1

                print()

        except Exception as e:
            print(f"   Error fetching adsets: {e}")
            logger.error(f"Error fetching adsets for campaign {campaign_id}: {e}")

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Instagram-only adsets: {instagram_only_count}")
    print(f"Automatic placement adsets: {automatic_count}")
    print(f"Active adsets with Facebook enabled: {facebook_active_count}")
    print(f"Paused adsets with Facebook configured: {facebook_paused_count}")
    print()

    if facebook_active_count > 0:
        print("⚠️  ACTION REQUIRED:")
        print(f"   {facebook_active_count} active adset(s) have Facebook enabled.")
        print("   If you want Instagram-only campaigns, edit these adsets in Meta Ads Manager:")
        print("   1. Go to Meta Ads Manager")
        print("   2. Edit the adset")
        print("   3. Under Placements, select 'Manual Placements'")
        print("   4. Uncheck Facebook and select only Instagram")
        print("   5. Save changes")
    else:
        print("✅ No active adsets with Facebook enabled")

    if automatic_count > 0:
        print()
        print("ℹ️  NOTE:")
        print(f"   {automatic_count} adset(s) use Automatic Placements (all platforms).")
        print("   These run on Facebook + Instagram + Audience Network + Messenger.")
        print("   Consider switching to Manual Placements for better control.")

    print("=" * 80)


def main():
    """Main execution flow"""
    parser = argparse.ArgumentParser(description='Meta Ads Platform Configuration Audit')
    parser.add_argument('--account', type=str, default='gre',
                       choices=['gre', 'upsc', 'test'],
                       help='Account to audit (default: gre)')

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info(f"Starting Platform Audit for {args.account}")
    logger.info("=" * 60)

    try:
        # Load configuration
        print(f"Loading configuration for {args.account} account...")
        config = load_account_config(args.account)

        # Initialize Facebook API
        print("Connecting to Meta Ads API...")
        FacebookAdsApi.init(access_token=config['access_token'])
        ad_account = AdAccount(config['account_id'])

        # Run audit
        audit_platforms(ad_account, config['account_name'])

        logger.info("Platform audit completed successfully")

    except ConfigurationError as e:
        print(str(e))
        logger.error(str(e))
        sys.exit(1)

    except Exception as e:
        error_msg = handle_meta_api_error(e)
        print(error_msg)
        logger.error(f"Error in main execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    from datetime import datetime  # Import here for log file naming
    main()
