#!/usr/bin/env python3
"""
Full settings audit for all active/paused campaigns, ad sets, and ads.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv('/Users/anigam/analytics/meta-slack-reporting/.env.upsc')

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad

access_token = os.getenv('META_ACCESS_TOKEN')
account_id = os.getenv('META_ADS_ACCOUNT_ID')

FacebookAdsApi.init(access_token=access_token)
ad_account = AdAccount(account_id)

def safe_json(obj):
    try:
        return json.dumps(dict(obj), indent=2)
    except:
        return str(obj)

def currency(val):
    if val is None:
        return "Not set"
    try:
        return f"₹{int(val)/100:,.2f}"
    except:
        return str(val)

# ═══════════════════════════════════════════════════════════════════════════════
# ACCOUNT
# ═══════════════════════════════════════════════════════════════════════════════
print("=" * 90)
print("ACCOUNT OVERVIEW")
print("=" * 90)

acct = ad_account.api_get(fields=[
    'name', 'account_status', 'balance', 'currency', 'spend_cap',
    'amount_spent', 'min_daily_budget', 'timezone_name',
    'disable_reason', 'funding_source_details', 'is_prepay_account',
    'owner', 'business_name', 'age',
])
info = dict(acct)
balance = float(info.get('balance', 0)) / 100
spend_cap = float(info.get('spend_cap', 0)) / 100
amount_spent = float(info.get('amount_spent', 0)) / 100
remaining = spend_cap - amount_spent
min_daily = float(info.get('min_daily_budget', 0)) / 100

status_map = {1: 'ACTIVE', 2: 'DISABLED', 3: 'UNSETTLED', 7: 'PENDING_RISK_REVIEW', 8: 'PENDING_SETTLEMENT', 9: 'IN_GRACE_PERIOD', 100: 'PENDING_CLOSURE', 101: 'CLOSED', 201: 'ANY_ACTIVE', 202: 'ANY_CLOSED'}
acct_status = status_map.get(info.get('account_status'), str(info.get('account_status')))

print(f"  Name: {info.get('name')}")
print(f"  Status: {acct_status}")
print(f"  Currency: {info.get('currency')}")
print(f"  Timezone: {info.get('timezone_name')}")
print(f"  Prepay Account: {info.get('is_prepay_account')}")
print(f"  Prepaid Balance: ₹{balance:,.2f}")
print(f"  Spend Cap: ₹{spend_cap:,.2f}")
print(f"  Total Spent (lifetime): ₹{amount_spent:,.2f}")
print(f"  Remaining: ₹{remaining:,.2f}")
print(f"  Min Daily Budget: ₹{min_daily:,.2f}")
print(f"  Account Age: {info.get('age', 'Unknown')}")
if info.get('disable_reason'):
    print(f"  ⚠️  Disable Reason: {info.get('disable_reason')}")

# ═══════════════════════════════════════════════════════════════════════════════
# CAMPAIGNS (ACTIVE ONLY)
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 90}")
print("ACTIVE CAMPAIGNS - Full Settings")
print("=" * 90)

campaigns = ad_account.get_campaigns(
    fields=[
        'name', 'id', 'status', 'effective_status', 'objective',
        'bid_strategy', 'daily_budget', 'lifetime_budget', 'budget_remaining',
        'spend_cap', 'buying_type', 'special_ad_categories',
        'start_time', 'stop_time', 'updated_time', 'created_time',
        'budget_rebalance_flag', 'can_use_spend_cap',
        'source_campaign_id', 'pacing_type',
    ],
    params={'effective_status': ['ACTIVE']}
)

campaign_map = {}
for c in campaigns:
    d = dict(c)
    cid = d.get('id')
    campaign_map[cid] = d.get('name', 'Unknown')

    print(f"\n  {'─' * 85}")
    print(f"  📢 {d.get('name')}")
    print(f"  ID: {cid}")
    print(f"  Status: {d.get('effective_status')}")
    print(f"  Objective: {d.get('objective')}")
    print(f"  Buying Type: {d.get('buying_type')}")
    print(f"  Bid Strategy: {d.get('bid_strategy', '⚠️  NOT SET (defaults to lowest cost)')}")
    print(f"  Daily Budget: {currency(d.get('daily_budget'))}")
    print(f"  Lifetime Budget: {currency(d.get('lifetime_budget'))}")
    print(f"  Budget Remaining: {currency(d.get('budget_remaining'))}")
    print(f"  Spend Cap: {currency(d.get('spend_cap'))}")
    print(f"  CBO (Budget Rebalance): {d.get('budget_rebalance_flag', 'Unknown')}")
    print(f"  Pacing: {d.get('pacing_type', 'Unknown')}")
    print(f"  Special Categories: {d.get('special_ad_categories', [])}")
    print(f"  Created: {d.get('created_time', 'Unknown')}")
    print(f"  Updated: {d.get('updated_time', 'Unknown')}")

# ═══════════════════════════════════════════════════════════════════════════════
# AD SETS (ACTIVE ONLY)
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 90}")
print("ACTIVE AD SETS - Full Settings")
print("=" * 90)

adsets = ad_account.get_ad_sets(
    fields=[
        'name', 'id', 'campaign_id', 'status', 'effective_status',
        'bid_amount', 'bid_strategy', 'billing_event',
        'optimization_goal', 'optimization_sub_event',
        'daily_budget', 'lifetime_budget', 'budget_remaining',
        'daily_min_spend_target', 'daily_spend_cap',
        'targeting', 'promoted_object', 'destination_type',
        'start_time', 'end_time', 'created_time', 'updated_time',
        'attribution_spec', 'pacing_type',
        'is_dynamic_creative', 'use_new_app_click',
        'learning_stage_info',
    ],
    params={'effective_status': ['ACTIVE']}
)

adset_map = {}
for a in adsets:
    d = dict(a)
    aid = d.get('id')
    cid = d.get('campaign_id')
    adset_map[aid] = d.get('name', 'Unknown')
    camp_name = campaign_map.get(cid, cid)

    print(f"\n  {'─' * 85}")
    print(f"  🎯 {d.get('name')}")
    print(f"  ID: {aid}")
    print(f"  Campaign: {camp_name}")
    print(f"  Status: {d.get('effective_status')}")

    # Bidding
    print(f"\n  ── Bidding & Optimization ──")
    print(f"  Bid Strategy: {d.get('bid_strategy', 'Inherited from campaign')}")
    bid_amt = d.get('bid_amount')
    print(f"  Bid Amount: {currency(bid_amt) if bid_amt else 'Auto (no manual bid)'}")
    print(f"  Billing Event: {d.get('billing_event')}")
    print(f"  Optimization Goal: {d.get('optimization_goal')}")
    opt_sub = d.get('optimization_sub_event')
    if opt_sub and opt_sub != 'NONE':
        print(f"  Optimization Sub-Event: {opt_sub}")
    print(f"  Pacing: {d.get('pacing_type', 'Unknown')}")

    # Learning phase
    learning = d.get('learning_stage_info', {})
    if learning:
        print(f"  Learning Phase: {learning}")

    # Budget
    print(f"\n  ── Budget ──")
    print(f"  Daily Budget: {currency(d.get('daily_budget')) if d.get('daily_budget') else 'Not set (CBO from campaign)'}")
    print(f"  Lifetime Budget: {currency(d.get('lifetime_budget')) if d.get('lifetime_budget') else 'Not set'}")
    print(f"  Budget Remaining: {currency(d.get('budget_remaining'))}")
    daily_min = d.get('daily_min_spend_target')
    daily_cap = d.get('daily_spend_cap')
    if daily_min:
        print(f"  Daily Min Spend Target: {currency(daily_min)}")
    if daily_cap:
        print(f"  Daily Spend Cap: {currency(daily_cap)}")

    # Targeting
    print(f"\n  ── Targeting ──")
    targeting = d.get('targeting', {})
    age_min = targeting.get('age_min', '?')
    age_max = targeting.get('age_max', '?')
    genders = targeting.get('genders', [])
    gender_str = {1: 'Male', 2: 'Female'}.get(genders[0], 'All') if genders else 'All'
    print(f"  Age: {age_min}-{age_max}")
    print(f"  Gender: {gender_str}")

    # Geo
    geo = targeting.get('geo_locations', {})
    countries = geo.get('countries', [])
    cities = [c.get('name', '') for c in geo.get('cities', [])]
    regions = [r.get('name', '') for r in geo.get('regions', [])]
    if countries:
        print(f"  Countries: {', '.join(countries)}")
    if regions:
        print(f"  Regions: {', '.join(regions)}")
    if cities:
        print(f"  Cities: {', '.join(cities)}")

    # Excluded geo
    excluded_geo = targeting.get('excluded_geo_locations', {})
    if excluded_geo:
        exc_cities = [c.get('name', '') for c in excluded_geo.get('cities', [])]
        exc_regions = [r.get('name', '') for r in excluded_geo.get('regions', [])]
        if exc_cities:
            print(f"  Excluded Cities: {', '.join(exc_cities)}")
        if exc_regions:
            print(f"  Excluded Regions: {', '.join(exc_regions)}")

    # Interests & behaviors
    flex_specs = targeting.get('flexible_spec', [])
    if flex_specs:
        for i, flex in enumerate(flex_specs):
            for key, vals in flex.items():
                if isinstance(vals, list):
                    names = [v.get('name', '') for v in vals if isinstance(v, dict)]
                    if names:
                        print(f"  {key.replace('_', ' ').title()}: {', '.join(names)}")

    # Exclusions
    exclusions = targeting.get('exclusions', {})
    if exclusions:
        for key, vals in exclusions.items():
            if isinstance(vals, list):
                names = [v.get('name', '') for v in vals if isinstance(v, dict)]
                if names:
                    print(f"  EXCLUDED {key}: {', '.join(names)}")

    # Custom audiences
    custom_auds = targeting.get('custom_audiences', [])
    if custom_auds:
        print(f"  Custom Audiences: {', '.join([a.get('name', a.get('id', '')) for a in custom_auds])}")
    excluded_auds = targeting.get('excluded_custom_audiences', [])
    if excluded_auds:
        print(f"  Excluded Custom Audiences: {', '.join([a.get('name', a.get('id', '')) for a in excluded_auds])}")

    # Device targeting
    user_os = targeting.get('user_os', [])
    user_device = targeting.get('user_device', [])
    publisher_platforms = targeting.get('publisher_platforms', [])
    facebook_positions = targeting.get('facebook_positions', [])
    instagram_positions = targeting.get('instagram_positions', [])
    device_platforms = targeting.get('device_platforms', [])

    if user_os:
        print(f"  OS: {', '.join(user_os)}")
    if user_device:
        print(f"  Devices: {', '.join(user_device)}")
    if publisher_platforms:
        print(f"  Platforms: {', '.join(publisher_platforms)}")
    if facebook_positions:
        print(f"  FB Positions: {', '.join(facebook_positions)}")
    if instagram_positions:
        print(f"  IG Positions: {', '.join(instagram_positions)}")
    if device_platforms:
        print(f"  Device Platforms: {', '.join(device_platforms)}")

    # Promoted object & destination
    print(f"\n  ── Conversion Setup ──")
    promoted = d.get('promoted_object', {})
    if promoted:
        try:
            print(f"  Promoted Object: {json.dumps(dict(promoted), indent=4)}")
        except:
            print(f"  Promoted Object: {str(promoted)}")
    dest = d.get('destination_type')
    if dest:
        print(f"  Destination Type: {dest}")

    # Attribution
    attribution = d.get('attribution_spec', [])
    if attribution:
        for attr in attribution:
            try:
                a_dict = dict(attr)
                print(f"  Attribution: {a_dict.get('event_type')} - {a_dict.get('window_days')} day(s)")
            except:
                print(f"  Attribution: {str(attr)}")

    # Dynamic creative
    if d.get('is_dynamic_creative'):
        print(f"  Dynamic Creative: YES")

    print(f"\n  Created: {d.get('created_time', 'Unknown')}")
    print(f"  Updated: {d.get('updated_time', 'Unknown')}")

# ═══════════════════════════════════════════════════════════════════════════════
# ADS (ACTIVE ONLY)
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 90}")
print("ACTIVE ADS - Creative & Status")
print("=" * 90)

ads = ad_account.get_ads(
    fields=[
        'name', 'id', 'adset_id', 'campaign_id',
        'status', 'effective_status',
        'creative', 'tracking_specs', 'conversion_specs',
        'created_time', 'updated_time',
    ],
    params={'effective_status': ['ACTIVE']}
)

for ad in ads:
    d = dict(ad)
    ad_id = d.get('id')
    adset_id = d.get('adset_id')
    cid = d.get('campaign_id')
    camp_name = campaign_map.get(cid, cid)
    adset_name = adset_map.get(adset_id, adset_id)

    print(f"\n  {'─' * 85}")
    print(f"  📄 {d.get('name')}")
    print(f"  ID: {ad_id}")
    print(f"  Campaign: {camp_name}")
    print(f"  Ad Set: {adset_name}")
    print(f"  Status: {d.get('effective_status')}")

    # Creative details
    creative_ref = d.get('creative', {})
    creative_id = creative_ref.get('id') if isinstance(creative_ref, dict) else None
    if creative_id:
        try:
            from facebook_business.adobjects.adcreative import AdCreative
            creative = AdCreative(creative_id).api_get(fields=[
                'name', 'title', 'body', 'call_to_action_type',
                'link_url', 'image_url', 'thumbnail_url',
                'video_id', 'object_type',
                'asset_feed_spec', 'object_story_spec',
                'url_tags',
            ])
            cr = dict(creative)
            print(f"  ── Creative ──")
            if cr.get('name'):
                print(f"  Creative Name: {cr.get('name')}")
            if cr.get('title'):
                print(f"  Title: {cr.get('title')}")
            if cr.get('body'):
                body = cr.get('body', '')
                print(f"  Body: {body[:120]}{'...' if len(body) > 120 else ''}")
            if cr.get('call_to_action_type'):
                print(f"  CTA: {cr.get('call_to_action_type')}")
            if cr.get('object_type'):
                print(f"  Object Type: {cr.get('object_type')}")
            if cr.get('link_url'):
                print(f"  Link: {cr.get('link_url')}")
            if cr.get('url_tags'):
                print(f"  URL Tags: {cr.get('url_tags')}")

            # Check object_story_spec for more details
            oss = cr.get('object_story_spec', {})
            if oss:
                try:
                    oss_dict = dict(oss)
                    page_id = oss_dict.get('page_id')
                    ig_id = oss_dict.get('instagram_actor_id')
                    if page_id:
                        print(f"  Page ID: {page_id}")
                    if ig_id:
                        print(f"  Instagram Actor: {ig_id}")
                    # Link data
                    link_data = oss_dict.get('link_data', {})
                    if link_data:
                        ld = dict(link_data) if hasattr(link_data, '__iter__') else link_data
                        if isinstance(ld, dict):
                            if ld.get('link'):
                                print(f"  Destination Link: {ld.get('link')}")
                            if ld.get('message'):
                                msg = ld.get('message', '')
                                print(f"  Ad Copy: {msg[:150]}{'...' if len(msg) > 150 else ''}")
                            cta = ld.get('call_to_action', {})
                            if cta:
                                try:
                                    cta_d = dict(cta)
                                    print(f"  CTA Type: {cta_d.get('type')}")
                                    cta_val = cta_d.get('value', {})
                                    if cta_val:
                                        try:
                                            cv = dict(cta_val)
                                            if cv.get('link'):
                                                print(f"  CTA Link: {cv.get('link')}")
                                            if cv.get('app_link'):
                                                print(f"  CTA App Link: {cv.get('app_link')}")
                                        except:
                                            print(f"  CTA Value: {str(cta_val)}")
                                except:
                                    print(f"  CTA: {str(cta)}")
                    # Video data
                    video_data = oss_dict.get('video_data', {})
                    if video_data:
                        vd = dict(video_data) if hasattr(video_data, '__iter__') else video_data
                        if isinstance(vd, dict):
                            if vd.get('video_id'):
                                print(f"  Video ID: {vd.get('video_id')}")
                            if vd.get('message'):
                                msg = vd.get('message', '')
                                print(f"  Video Copy: {msg[:150]}{'...' if len(msg) > 150 else ''}")
                except:
                    pass

        except Exception as e:
            print(f"  Creative ID: {creative_id} (error fetching details: {e})")

    # Tracking
    tracking = d.get('tracking_specs', [])
    if tracking:
        for ts in tracking:
            try:
                print(f"  Tracking: {dict(ts)}")
            except:
                print(f"  Tracking: {str(ts)}")

    print(f"  Created: {d.get('created_time', 'Unknown')}")

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 90}")
print("SUMMARY")
print("=" * 90)
print(f"  Active Campaigns: {len(campaign_map)}")
print(f"  Active Ad Sets: {len(adset_map)}")
print(f"  Active Ads: {sum(1 for _ in ads)}")
print(f"  Account Balance: ₹{balance:,.2f}")
print(f"  Remaining Budget: ₹{remaining:,.2f}")
print(f"  Daily Burn Rate (sum of daily budgets): ₹{sum(int(dict(c).get('daily_budget', 0))/100 for c in campaigns):,.2f}")
print(f"\nDone.")
