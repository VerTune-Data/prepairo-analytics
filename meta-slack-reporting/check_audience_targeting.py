#!/usr/bin/env python3
"""
Check audience targeting issues: frequency, overlap, CPM trends, audience size
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('/Users/anigam/analytics/meta-slack-reporting/.env.upsc')

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.campaign import Campaign

access_token = os.getenv('META_ACCESS_TOKEN')
account_id = os.getenv('META_ADS_ACCOUNT_ID')

FacebookAdsApi.init(access_token=access_token)
ad_account = AdAccount(account_id)

print("=" * 90)
print("AUDIENCE & TARGETING DEEP DIVE")
print("=" * 90)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. FREQUENCY & REACH DATA (daily breakdown for last 7 days)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 90)
print("1. DAILY FREQUENCY, CPM & REACH BY CAMPAIGN (Last 7 Days)")
print("─" * 90)

end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

try:
    insights = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'time_increment': 1,
        'level': 'campaign',
        'fields': [
            'campaign_name', 'campaign_id',
            'spend', 'impressions', 'reach', 'frequency',
            'cpm', 'clicks', 'ctr',
            'actions', 'cost_per_action_type',
        ],
        'filtering': [{'field': 'campaign.effective_status', 'operator': 'IN', 'value': ['ACTIVE']}]
    })

    # Group by campaign
    by_campaign = {}
    for row in insights:
        d = dict(row)
        cname = d.get('campaign_name', 'Unknown')
        if cname not in by_campaign:
            by_campaign[cname] = []
        by_campaign[cname].append(d)

    for cname, rows in by_campaign.items():
        print(f"\n  📢 {cname}")
        print(f"  {'Date':<12} {'Spend':>8} {'Impress':>9} {'Reach':>8} {'Freq':>6} {'CPM':>8} {'Clicks':>7} {'CTR':>6}")
        print(f"  {'─'*12} {'─'*8} {'─'*9} {'─'*8} {'─'*6} {'─'*8} {'─'*7} {'─'*6}")
        for r in sorted(rows, key=lambda x: x.get('date_start', '')):
            date = r.get('date_start', '')
            spend = float(r.get('spend', 0))
            imps = int(r.get('impressions', 0))
            reach = int(r.get('reach', 0))
            freq = float(r.get('frequency', 0))
            cpm = float(r.get('cpm', 0))
            clicks = int(r.get('clicks', 0))
            ctr = float(r.get('ctr', 0))

            freq_warn = " ⚠️" if freq > 2.0 else ""
            cpm_warn = " 🔴" if cpm > 45 else ""

            print(f"  {date:<12} ₹{spend:>6.0f} {imps:>9,} {reach:>8,} {freq:>5.2f}{freq_warn} ₹{cpm:>6.1f}{cpm_warn} {clicks:>7,} {ctr:>5.2f}%")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. AD SET LEVEL FREQUENCY & CPM
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 90)
print("2. AD SET LEVEL - FREQUENCY & CPM (Last 7 Days Aggregate)")
print("─" * 90)

try:
    adset_insights = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'adset',
        'fields': [
            'adset_name', 'adset_id', 'campaign_name',
            'spend', 'impressions', 'reach', 'frequency',
            'cpm', 'clicks', 'ctr',
        ],
        'filtering': [{'field': 'adset.effective_status', 'operator': 'IN', 'value': ['ACTIVE']}]
    })

    print(f"\n  {'Ad Set':<40} {'Spend':>8} {'Reach':>8} {'Freq':>6} {'CPM':>8} {'CTR':>6}")
    print(f"  {'─'*40} {'─'*8} {'─'*8} {'─'*6} {'─'*8} {'─'*6}")

    for row in adset_insights:
        d = dict(row)
        name = d.get('adset_name', 'Unknown')[:40]
        spend = float(d.get('spend', 0))
        reach = int(d.get('reach', 0))
        freq = float(d.get('frequency', 0))
        cpm = float(d.get('cpm', 0))
        ctr = float(d.get('ctr', 0))

        freq_warn = " ⚠️" if freq > 2.5 else ""
        cpm_warn = " 🔴" if cpm > 45 else ""

        print(f"  {name:<40} ₹{spend:>6.0f} {reach:>8,} {freq:>5.2f}{freq_warn} ₹{cpm:>6.1f}{cpm_warn} {ctr:>5.2f}%")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. AUDIENCE SIZE ESTIMATES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 90)
print("3. AUDIENCE SIZE & SATURATION CHECK")
print("─" * 90)

try:
    adsets = ad_account.get_ad_sets(
        fields=['name', 'id', 'campaign_id', 'targeting', 'effective_status'],
        params={'effective_status': ['ACTIVE']}
    )

    for a in adsets:
        d = dict(a)
        name = d.get('name')
        targeting = d.get('targeting', {})

        # Try to get reach estimate
        try:
            reach_est = ad_account.get_reach_estimate(params={
                'targeting_spec': targeting,
                'optimization_goal': 'REACH',
            })
            for est in reach_est:
                est_d = dict(est)
                users_lower = est_d.get('users_lower_bound', 0)
                users_upper = est_d.get('users_upper_bound', 0)
                print(f"\n  🎯 {name}")
                print(f"  Estimated Audience: {users_lower:,} - {users_upper:,} people")
        except Exception as e:
            print(f"\n  🎯 {name}")
            print(f"  Reach estimate: {e}")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. AD-LEVEL FREQUENCY (which ads are burning out?)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 90)
print("4. AD-LEVEL FREQUENCY CHECK (Which Ads Are Fatigued?)")
print("─" * 90)

try:
    ad_insights = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'ad',
        'fields': [
            'ad_name', 'adset_name', 'campaign_name',
            'spend', 'impressions', 'reach', 'frequency',
            'cpm', 'ctr', 'actions',
        ],
        'filtering': [{'field': 'ad.effective_status', 'operator': 'IN', 'value': ['ACTIVE']}],
        'sort': ['spend_descending'],
    })

    print(f"\n  {'Ad Name':<55} {'Spend':>7} {'Freq':>5} {'CPM':>7} {'CTR':>6}")
    print(f"  {'─'*55} {'─'*7} {'─'*5} {'─'*7} {'─'*6}")

    for row in ad_insights:
        d = dict(row)
        name = d.get('ad_name', 'Unknown')[:55]
        spend = float(d.get('spend', 0))
        freq = float(d.get('frequency', 0))
        cpm = float(d.get('cpm', 0))
        ctr = float(d.get('ctr', 0))

        freq_flag = "🔴" if freq > 3.0 else "⚠️" if freq > 2.0 else "✅"
        print(f"  {name:<55} ₹{spend:>5.0f} {freq:>4.2f}{freq_flag} ₹{cpm:>5.1f} {ctr:>5.2f}%")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. PLACEMENT BREAKDOWN (where is money going?)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 90)
print("5. PLACEMENT BREAKDOWN (Where Is Budget Going?)")
print("─" * 90)

try:
    placement_insights = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'account',
        'breakdowns': ['publisher_platform', 'platform_position'],
        'fields': [
            'spend', 'impressions', 'reach', 'cpm', 'clicks', 'ctr',
        ],
        'filtering': [{'field': 'campaign.effective_status', 'operator': 'IN', 'value': ['ACTIVE']}]
    })

    print(f"\n  {'Platform':<15} {'Position':<25} {'Spend':>8} {'Impress':>9} {'CPM':>8} {'CTR':>6}")
    print(f"  {'─'*15} {'─'*25} {'─'*8} {'─'*9} {'─'*8} {'─'*6}")

    for row in placement_insights:
        d = dict(row)
        platform = d.get('publisher_platform', 'Unknown')
        position = d.get('platform_position', 'Unknown')
        spend = float(d.get('spend', 0))
        imps = int(d.get('impressions', 0))
        cpm = float(d.get('cpm', 0))
        ctr = float(d.get('ctr', 0))

        print(f"  {platform:<15} {position:<25} ₹{spend:>6.0f} {imps:>9,} ₹{cpm:>6.1f} {ctr:>5.2f}%")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. AGE & GENDER BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 90)
print("6. AGE & GENDER BREAKDOWN (Who Is Seeing Your Ads?)")
print("─" * 90)

try:
    demo_insights = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'account',
        'breakdowns': ['age', 'gender'],
        'fields': [
            'spend', 'impressions', 'reach', 'cpm', 'clicks', 'ctr', 'actions',
        ],
        'filtering': [{'field': 'campaign.effective_status', 'operator': 'IN', 'value': ['ACTIVE']}]
    })

    print(f"\n  {'Age':<8} {'Gender':<8} {'Spend':>8} {'Reach':>8} {'CPM':>8} {'CTR':>6} {'Installs':>9}")
    print(f"  {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*6} {'─'*9}")

    for row in demo_insights:
        d = dict(row)
        age = d.get('age', '?')
        gender = d.get('gender', '?')
        spend = float(d.get('spend', 0))
        reach = int(d.get('reach', 0))
        cpm = float(d.get('cpm', 0))
        ctr = float(d.get('ctr', 0))

        # Extract installs from actions
        installs = 0
        actions = d.get('actions', [])
        for action in actions:
            if action.get('action_type') in ['app_install', 'mobile_app_install']:
                installs = int(action.get('value', 0))

        print(f"  {age:<8} {gender:<8} ₹{spend:>6.0f} {reach:>8,} ₹{cpm:>6.1f} {ctr:>5.2f}% {installs:>9}")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. DEVICE & OS BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 90)
print("7. DEVICE BREAKDOWN")
print("─" * 90)

try:
    device_insights = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'account',
        'breakdowns': ['device_platform'],
        'fields': [
            'spend', 'impressions', 'reach', 'cpm', 'clicks', 'ctr',
        ],
        'filtering': [{'field': 'campaign.effective_status', 'operator': 'IN', 'value': ['ACTIVE']}]
    })

    print(f"\n  {'Device':<15} {'Spend':>8} {'Impress':>9} {'CPM':>8} {'CTR':>6}")
    print(f"  {'─'*15} {'─'*8} {'─'*9} {'─'*8} {'─'*6}")

    for row in device_insights:
        d = dict(row)
        device = d.get('device_platform', 'Unknown')
        spend = float(d.get('spend', 0))
        imps = int(d.get('impressions', 0))
        cpm = float(d.get('cpm', 0))
        ctr = float(d.get('ctr', 0))

        print(f"  {device:<15} ₹{spend:>6.0f} {imps:>9,} ₹{cpm:>6.1f} {ctr:>5.2f}%")

except Exception as e:
    print(f"  ERROR: {e}")


print(f"\n{'=' * 90}")
print("Done.")
