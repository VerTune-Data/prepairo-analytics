#!/usr/bin/env python3
"""
Pinpoint exactly which campaign/adset/ad is leaking budget to Audience Network,
age 35+, and expensive placements.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('/Users/anigam/analytics/meta-slack-reporting/.env.upsc')

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

access_token = os.getenv('META_ACCESS_TOKEN')
account_id = os.getenv('META_ADS_ACCOUNT_ID')

FacebookAdsApi.init(access_token=access_token)
ad_account = AdAccount(account_id)

end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
active_filter = [{'field': 'campaign.effective_status', 'operator': 'IN', 'value': ['ACTIVE']}]

print("=" * 100)
print("PINPOINT: WHERE IS BUDGET LEAKING?")
print(f"Period: {start_date} to {end_date}")
print("=" * 100)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. PLACEMENT BY CAMPAIGN
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 100)
print("1. PLACEMENT SPEND BY CAMPAIGN")
print("─" * 100)

try:
    rows = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'campaign',
        'breakdowns': ['publisher_platform'],
        'fields': ['campaign_name', 'campaign_id', 'spend', 'impressions', 'cpm', 'clicks', 'ctr', 'actions'],
        'filtering': active_filter,
    })

    by_camp = {}
    for r in rows:
        d = dict(r)
        cname = d.get('campaign_name', '?')
        platform = d.get('publisher_platform', '?')
        if cname not in by_camp:
            by_camp[cname] = []
        by_camp[cname].append(d)

    for cname, items in by_camp.items():
        total_spend = sum(float(i.get('spend', 0)) for i in items)
        print(f"\n  📢 {cname} (Total: ₹{total_spend:,.0f})")
        print(f"  {'Platform':<20} {'Spend':>8} {'%':>5} {'Impress':>9} {'CPM':>8} {'Clicks':>7} {'CTR':>6}")
        print(f"  {'─'*20} {'─'*8} {'─'*5} {'─'*9} {'─'*8} {'─'*7} {'─'*6}")
        for i in sorted(items, key=lambda x: float(x.get('spend', 0)), reverse=True):
            plat = i.get('publisher_platform', '?')
            spend = float(i.get('spend', 0))
            imps = int(i.get('impressions', 0))
            cpm = float(i.get('cpm', 0))
            clicks = int(i.get('clicks', 0))
            ctr = float(i.get('ctr', 0))
            pct = (spend / total_spend * 100) if total_spend > 0 else 0
            warn = " 🔴 WASTE" if plat == 'audience_network' else ""
            print(f"  {plat:<20} ₹{spend:>6,.0f} {pct:>4.0f}% {imps:>9,} ₹{cpm:>6.1f} {clicks:>7,} {ctr:>5.1f}%{warn}")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. PLACEMENT BY AD SET
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 100)
print("2. PLACEMENT SPEND BY AD SET")
print("─" * 100)

try:
    rows = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'adset',
        'breakdowns': ['publisher_platform'],
        'fields': ['adset_name', 'campaign_name', 'spend', 'impressions', 'cpm', 'clicks', 'ctr'],
        'filtering': active_filter,
    })

    by_adset = {}
    for r in rows:
        d = dict(r)
        aname = d.get('adset_name', '?')
        if aname not in by_adset:
            by_adset[aname] = {'campaign': d.get('campaign_name', '?'), 'items': []}
        by_adset[aname]['items'].append(d)

    for aname, data in by_adset.items():
        items = data['items']
        total_spend = sum(float(i.get('spend', 0)) for i in items)
        print(f"\n  🎯 {aname}")
        print(f"     Campaign: {data['campaign']}")
        print(f"     Total: ₹{total_spend:,.0f}")
        print(f"     {'Platform':<20} {'Spend':>8} {'%':>5} {'CPM':>8} {'Clicks':>7} {'CTR':>6}")
        print(f"     {'─'*20} {'─'*8} {'─'*5} {'─'*8} {'─'*7} {'─'*6}")
        for i in sorted(items, key=lambda x: float(x.get('spend', 0)), reverse=True):
            plat = i.get('publisher_platform', '?')
            spend = float(i.get('spend', 0))
            cpm = float(i.get('cpm', 0))
            clicks = int(i.get('clicks', 0))
            ctr = float(i.get('ctr', 0))
            pct = (spend / total_spend * 100) if total_spend > 0 else 0
            warn = " 🔴" if plat == 'audience_network' else ""
            print(f"     {plat:<20} ₹{spend:>6,.0f} {pct:>4.0f}% ₹{cpm:>6.1f} {clicks:>7,} {ctr:>5.1f}%{warn}")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. PLACEMENT BY INDIVIDUAL AD
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 100)
print("3. AUDIENCE NETWORK SPEND BY INDIVIDUAL AD")
print("─" * 100)

try:
    rows = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'ad',
        'breakdowns': ['publisher_platform'],
        'fields': ['ad_name', 'adset_name', 'campaign_name', 'spend', 'impressions', 'cpm', 'clicks', 'ctr'],
        'filtering': active_filter,
    })

    an_ads = []
    for r in rows:
        d = dict(r)
        if d.get('publisher_platform') == 'audience_network':
            an_ads.append(d)

    if an_ads:
        an_ads.sort(key=lambda x: float(x.get('spend', 0)), reverse=True)
        print(f"\n  Ads spending on Audience Network:")
        print(f"  {'Ad Name':<50} {'Ad Set':<35} {'Spend':>7} {'CPM':>7} {'CTR':>6}")
        print(f"  {'─'*50} {'─'*35} {'─'*7} {'─'*7} {'─'*6}")
        for d in an_ads:
            name = d.get('ad_name', '?')[:50]
            adset = d.get('adset_name', '?')[:35]
            spend = float(d.get('spend', 0))
            cpm = float(d.get('cpm', 0))
            ctr = float(d.get('ctr', 0))
            print(f"  {name:<50} {adset:<35} ₹{spend:>5,.0f} ₹{cpm:>5.1f} {ctr:>5.1f}%")
    else:
        print("  No Audience Network spend found at ad level.")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. AGE BREAKDOWN BY CAMPAIGN
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 100)
print("4. AGE SPEND BY CAMPAIGN (Where is 35+ waste?)")
print("─" * 100)

try:
    rows = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'campaign',
        'breakdowns': ['age'],
        'fields': ['campaign_name', 'spend', 'impressions', 'reach', 'cpm', 'clicks', 'ctr', 'actions'],
        'filtering': active_filter,
    })

    by_camp = {}
    for r in rows:
        d = dict(r)
        cname = d.get('campaign_name', '?')
        if cname not in by_camp:
            by_camp[cname] = []
        by_camp[cname].append(d)

    for cname, items in by_camp.items():
        total_spend = sum(float(i.get('spend', 0)) for i in items)
        print(f"\n  📢 {cname} (Total: ₹{total_spend:,.0f})")
        print(f"  {'Age':<8} {'Spend':>8} {'%':>5} {'Reach':>8} {'CPM':>8} {'CTR':>6} {'Installs':>9}")
        print(f"  {'─'*8} {'─'*8} {'─'*5} {'─'*8} {'─'*8} {'─'*6} {'─'*9}")

        waste_35plus = 0
        for i in sorted(items, key=lambda x: x.get('age', '')):
            age = i.get('age', '?')
            spend = float(i.get('spend', 0))
            reach = int(i.get('reach', 0))
            cpm = float(i.get('cpm', 0))
            ctr = float(i.get('ctr', 0))
            pct = (spend / total_spend * 100) if total_spend > 0 else 0

            installs = 0
            for a in i.get('actions', []):
                if a.get('action_type') in ['app_install', 'mobile_app_install']:
                    installs = int(a.get('value', 0))

            # Check if 35+
            is_old = age in ['35-44', '45-54', '55-64', '65+']
            if is_old:
                waste_35plus += spend
            warn = " ⬅️ WASTE" if is_old and installs == 0 else ""
            print(f"  {age:<8} ₹{spend:>6,.0f} {pct:>4.0f}% {reach:>8,} ₹{cpm:>6.1f} {ctr:>5.1f}% {installs:>9}{warn}")

        if waste_35plus > 0:
            print(f"  ⚠️  35+ waste: ₹{waste_35plus:,.0f} ({waste_35plus/total_spend*100:.0f}% of campaign)")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. AGE BREAKDOWN BY AD SET
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 100)
print("5. AGE SPEND BY AD SET")
print("─" * 100)

try:
    rows = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'adset',
        'breakdowns': ['age'],
        'fields': ['adset_name', 'campaign_name', 'spend', 'reach', 'cpm', 'ctr', 'actions'],
        'filtering': active_filter,
    })

    by_adset = {}
    for r in rows:
        d = dict(r)
        aname = d.get('adset_name', '?')
        if aname not in by_adset:
            by_adset[aname] = {'campaign': d.get('campaign_name', '?'), 'items': []}
        by_adset[aname]['items'].append(d)

    for aname, data in by_adset.items():
        items = data['items']
        total = sum(float(i.get('spend', 0)) for i in items)
        print(f"\n  🎯 {aname} ({data['campaign']})")
        print(f"  {'Age':<8} {'Spend':>8} {'%':>5} {'Reach':>8} {'CPM':>8} {'Installs':>9}")
        print(f"  {'─'*8} {'─'*8} {'─'*5} {'─'*8} {'─'*8} {'─'*9}")

        waste = 0
        for i in sorted(items, key=lambda x: x.get('age', '')):
            age = i.get('age', '?')
            spend = float(i.get('spend', 0))
            reach = int(i.get('reach', 0))
            cpm = float(i.get('cpm', 0))
            pct = (spend / total * 100) if total > 0 else 0
            installs = 0
            for a in i.get('actions', []):
                if a.get('action_type') in ['app_install', 'mobile_app_install']:
                    installs = int(a.get('value', 0))
            is_old = age in ['35-44', '45-54', '55-64', '65+']
            if is_old:
                waste += spend
            flag = " 🔴" if is_old and installs == 0 else ""
            print(f"  {age:<8} ₹{spend:>6,.0f} {pct:>4.0f}% {reach:>8,} ₹{cpm:>6.1f} {installs:>9}{flag}")
        if waste > 0:
            print(f"  ⚠️  35+ waste: ₹{waste:,.0f}")

except Exception as e:
    print(f"  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. PLACEMENT x POSITION BY AD SET (detailed)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 100)
print("6. DETAILED POSITION SPEND BY AD SET")
print("─" * 100)

try:
    rows = ad_account.get_insights(params={
        'time_range': {'since': start_date, 'until': end_date},
        'level': 'adset',
        'breakdowns': ['publisher_platform', 'platform_position'],
        'fields': ['adset_name', 'campaign_name', 'spend', 'impressions', 'cpm', 'clicks', 'ctr'],
        'filtering': active_filter,
    })

    by_adset = {}
    for r in rows:
        d = dict(r)
        aname = d.get('adset_name', '?')
        if aname not in by_adset:
            by_adset[aname] = []
        by_adset[aname].append(d)

    for aname, items in by_adset.items():
        total = sum(float(i.get('spend', 0)) for i in items)
        print(f"\n  🎯 {aname} (₹{total:,.0f})")
        print(f"  {'Platform':<18} {'Position':<28} {'Spend':>7} {'%':>5} {'CPM':>7} {'CTR':>6}")
        print(f"  {'─'*18} {'─'*28} {'─'*7} {'─'*5} {'─'*7} {'─'*6}")
        for i in sorted(items, key=lambda x: float(x.get('spend', 0)), reverse=True):
            plat = i.get('publisher_platform', '?')
            pos = i.get('platform_position', '?')
            spend = float(i.get('spend', 0))
            cpm = float(i.get('cpm', 0))
            ctr = float(i.get('ctr', 0))
            pct = (spend / total * 100) if total > 0 else 0
            warn = " 🔴" if plat == 'audience_network' else ""
            if spend >= 1:  # skip tiny amounts
                print(f"  {plat:<18} {pos:<28} ₹{spend:>5,.0f} {pct:>4.0f}% ₹{cpm:>5.1f} {ctr:>5.1f}%{warn}")

except Exception as e:
    print(f"  ERROR: {e}")

print(f"\n{'=' * 100}")
print("Done.")
