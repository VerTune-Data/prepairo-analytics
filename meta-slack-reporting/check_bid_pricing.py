#!/usr/bin/env python3
"""
Ad-hoc script to check bid strategy, pricing, budgets, and optimization settings
for all campaigns and ad sets in the Meta Ads account.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load UPSC account config
load_dotenv('/Users/anigam/analytics/meta-slack-reporting/.env.upsc')

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet

# Init API
access_token = os.getenv('META_ACCESS_TOKEN')
account_id = os.getenv('META_ADS_ACCOUNT_ID')

FacebookAdsApi.init(access_token=access_token)
ad_account = AdAccount(account_id)

print(f"{'='*80}")
print(f"META ADS BID & PRICING CHECK - {os.getenv('ACCOUNT_NAME', 'Unknown')}")
print(f"Account: {account_id}")
print(f"{'='*80}\n")

# ── CAMPAIGNS ──────────────────────────────────────────────────────────────────
print("CAMPAIGNS - Bid Strategy & Budget")
print("-" * 80)

campaign_fields = [
    'name',
    'status',
    'effective_status',
    'objective',
    'bid_strategy',
    'daily_budget',
    'lifetime_budget',
    'budget_remaining',
    'spend_cap',
    'special_ad_categories',
    'buying_type',
    'start_time',
    'updated_time',
]

try:
    campaigns = ad_account.get_campaigns(
        fields=campaign_fields,
        params={'effective_status': ['ACTIVE', 'PAUSED']}
    )

    for c in campaigns:
        data = dict(c)
        name = data.get('name', 'Unknown')
        status = data.get('effective_status', 'Unknown')
        objective = data.get('objective', 'Unknown')
        bid_strategy = data.get('bid_strategy', 'NOT SET (defaults to LOWEST_COST)')
        daily_budget = data.get('daily_budget')
        lifetime_budget = data.get('lifetime_budget')
        budget_remaining = data.get('budget_remaining')
        spend_cap = data.get('spend_cap')
        buying_type = data.get('buying_type', 'Unknown')
        special_cats = data.get('special_ad_categories', [])

        # Convert cents to rupees
        daily_budget_rs = f"₹{int(daily_budget)/100:,.2f}" if daily_budget else "Not set"
        lifetime_budget_rs = f"₹{int(lifetime_budget)/100:,.2f}" if lifetime_budget else "Not set"
        budget_remaining_rs = f"₹{int(budget_remaining)/100:,.2f}" if budget_remaining else "N/A"
        spend_cap_rs = f"₹{int(spend_cap)/100:,.2f}" if spend_cap else "No cap"

        print(f"\n  Campaign: {name}")
        print(f"  Status: {status}")
        print(f"  Objective: {objective}")
        print(f"  Buying Type: {buying_type}")
        print(f"  Bid Strategy: {bid_strategy}")
        print(f"  Daily Budget: {daily_budget_rs}")
        print(f"  Lifetime Budget: {lifetime_budget_rs}")
        print(f"  Budget Remaining: {budget_remaining_rs}")
        print(f"  Spend Cap: {spend_cap_rs}")
        if special_cats:
            print(f"  Special Ad Categories: {special_cats}")
        print()

except Exception as e:
    print(f"  ERROR fetching campaigns: {e}\n")

# ── AD SETS ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("AD SETS - Bid Amount, Optimization & Targeting")
print("-" * 80)

adset_fields = [
    'name',
    'campaign_id',
    'status',
    'effective_status',
    'bid_amount',
    'bid_strategy',
    'billing_event',
    'optimization_goal',
    'optimization_sub_event',
    'daily_budget',
    'lifetime_budget',
    'budget_remaining',
    'targeting',
    'promoted_object',
    'destination_type',
    'start_time',
    'end_time',
    'daily_min_spend_target',
    'daily_spend_cap',
    'attribution_spec',
]

try:
    adsets = ad_account.get_ad_sets(
        fields=adset_fields,
        params={'effective_status': ['ACTIVE', 'PAUSED']}
    )

    for a in adsets:
        data = dict(a)
        name = data.get('name', 'Unknown')
        campaign_id = data.get('campaign_id', '')
        status = data.get('effective_status', 'Unknown')
        bid_amount = data.get('bid_amount')
        bid_strategy = data.get('bid_strategy', 'Inherited from campaign')
        billing_event = data.get('billing_event', 'Unknown')
        opt_goal = data.get('optimization_goal', 'Unknown')
        opt_sub = data.get('optimization_sub_event', '')
        daily_budget = data.get('daily_budget')
        lifetime_budget = data.get('lifetime_budget')
        budget_remaining = data.get('budget_remaining')
        promoted_obj = data.get('promoted_object', {})
        dest_type = data.get('destination_type', '')
        daily_min = data.get('daily_min_spend_target')
        daily_cap = data.get('daily_spend_cap')
        attribution = data.get('attribution_spec', [])

        # Convert cents to rupees
        bid_amount_rs = f"₹{int(bid_amount)/100:,.2f}" if bid_amount else "Auto (no manual bid)"
        daily_budget_rs = f"₹{int(daily_budget)/100:,.2f}" if daily_budget else "Not set (CBO)"
        lifetime_budget_rs = f"₹{int(lifetime_budget)/100:,.2f}" if lifetime_budget else "Not set"
        budget_remaining_rs = f"₹{int(budget_remaining)/100:,.2f}" if budget_remaining else "N/A"
        daily_min_rs = f"₹{int(daily_min)/100:,.2f}" if daily_min else "None"
        daily_cap_rs = f"₹{int(daily_cap)/100:,.2f}" if daily_cap else "None"

        # Extract targeting summary
        targeting = data.get('targeting', {})
        age_min = targeting.get('age_min', '?')
        age_max = targeting.get('age_max', '?')
        genders = targeting.get('genders', [])
        gender_str = {1: 'Male', 2: 'Female'}.get(genders[0], 'All') if genders else 'All'
        geo_locations = targeting.get('geo_locations', {})
        countries = geo_locations.get('countries', [])
        cities = [c.get('name', '') for c in geo_locations.get('cities', [])]

        # Interests/behaviors
        interests = targeting.get('flexible_spec', [])
        interest_names = []
        for flex in interests:
            for key, vals in flex.items():
                if isinstance(vals, list):
                    for v in vals:
                        if isinstance(v, dict):
                            interest_names.append(v.get('name', ''))

        print(f"\n  Ad Set: {name}")
        print(f"  Campaign ID: {campaign_id}")
        print(f"  Status: {status}")
        print(f"  ── Bidding ──")
        print(f"  Bid Strategy: {bid_strategy}")
        print(f"  Bid Amount: {bid_amount_rs}")
        print(f"  Billing Event: {billing_event}")
        print(f"  Optimization Goal: {opt_goal}")
        if opt_sub:
            print(f"  Optimization Sub-Event: {opt_sub}")
        print(f"  ── Budget ──")
        print(f"  Daily Budget: {daily_budget_rs}")
        print(f"  Lifetime Budget: {lifetime_budget_rs}")
        print(f"  Budget Remaining: {budget_remaining_rs}")
        print(f"  Daily Min Spend: {daily_min_rs}")
        print(f"  Daily Spend Cap: {daily_cap_rs}")
        print(f"  ── Targeting ──")
        print(f"  Age: {age_min}-{age_max} | Gender: {gender_str}")
        if countries:
            print(f"  Countries: {', '.join(countries)}")
        if cities:
            print(f"  Cities: {', '.join(cities[:10])}")
        if interest_names:
            print(f"  Interests: {', '.join(interest_names[:10])}")
        if promoted_obj:
            try:
                print(f"  Promoted Object: {json.dumps(dict(promoted_obj), indent=4)}")
            except (TypeError, ValueError):
                print(f"  Promoted Object: {str(promoted_obj)}")
        if dest_type:
            print(f"  Destination: {dest_type}")
        if attribution:
            print(f"  Attribution: {json.dumps(attribution)}")
        print()

except Exception as e:
    print(f"  ERROR fetching ad sets: {e}\n")

# ── ACCOUNT LEVEL ──────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("ACCOUNT - Balance & Spend")
print("-" * 80)

try:
    account_info = ad_account.api_get(
        fields=[
            'account_id', 'name', 'account_status', 'balance', 'currency',
            'spend_cap', 'amount_spent', 'min_campaign_group_spend_cap',
            'min_daily_budget', 'timezone_name', 'funding_source',
            'business_name', 'owner',
        ]
    )

    info = dict(account_info)
    balance = float(info.get('balance', 0)) / 100
    spend_cap = float(info.get('spend_cap', 0)) / 100
    amount_spent = float(info.get('amount_spent', 0)) / 100
    remaining = spend_cap - amount_spent
    min_daily = float(info.get('min_daily_budget', 0)) / 100

    print(f"\n  Account: {info.get('name', 'Unknown')}")
    print(f"  Status: {info.get('account_status', 'Unknown')}")
    print(f"  Currency: {info.get('currency', 'Unknown')}")
    print(f"  Timezone: {info.get('timezone_name', 'Unknown')}")
    print(f"  Business: {info.get('business_name', 'N/A')}")
    print(f"  Prepaid Balance: ₹{balance:,.2f}")
    print(f"  Spend Cap: ₹{spend_cap:,.2f}")
    print(f"  Total Spent: ₹{amount_spent:,.2f}")
    print(f"  Remaining Budget: ₹{remaining:,.2f}")
    print(f"  Min Daily Budget: ₹{min_daily:,.2f}")

except Exception as e:
    print(f"  ERROR fetching account info: {e}\n")

print(f"\n{'='*80}")
print("Done.")
