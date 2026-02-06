#!/usr/bin/env python3
"""Analyze historical ad performance"""
import sqlite3
import json
from collections import defaultdict

conn = sqlite3.connect("meta_ads_history.db")
cursor = conn.cursor()

# Get all snapshots
cursor.execute("SELECT id, date_since, created_at, campaigns_json FROM snapshots ORDER BY created_at ASC")
rows = cursor.fetchall()

print("=== HISTORICAL TREND ===")
print()

# Track unique dates and their best data
daily_best = {}

for snap_id, date_since, created_at, campaigns_json in rows:
    date_key = date_since[:10] if date_since else created_at[:10]

    if not campaigns_json:
        continue

    campaigns = json.loads(campaigns_json)

    day_spend = 0
    day_imps = 0
    day_clicks = 0
    day_installs = 0
    day_regs = 0

    for c in campaigns:
        day_spend += float(c.get("spend", 0) or 0)
        day_imps += int(c.get("impressions", 0) or 0)
        day_clicks += int(c.get("clicks", 0) or 0)

        actions = c.get("actions", []) or []
        for a in actions:
            t = a.get("action_type", "")
            v = int(float(a.get("value", 0) or 0))
            if t in ["omni_app_install", "mobile_app_install", "app_install"]:
                day_installs += v
            if t in ["omni_complete_registration", "complete_registration"]:
                day_regs += v

    # Keep latest snapshot for each day
    daily_best[date_key] = {
        "spend": day_spend,
        "imps": day_imps,
        "clicks": day_clicks,
        "installs": day_installs,
        "regs": day_regs
    }

print("Date        |    Spend |  Impressions |  Clicks |   CTR | Installs | Regs |     CPI")
print("-" * 90)

for date in sorted(daily_best.keys()):
    d = daily_best[date]
    ctr = (d["clicks"]/d["imps"]*100) if d["imps"] > 0 else 0
    cpi = d["spend"]/d["installs"] if d["installs"] > 0 else 0

    # Highlight issues
    flag = ""
    if d["installs"] == 0 and d["spend"] > 500:
        flag = " ⚠️ NO INSTALLS"
    elif cpi > 200 and d["installs"] > 0:
        flag = " 🔴 HIGH CPI"

    print(f"{date} | Rs {d['spend']:>5,.0f} | {d['imps']:>12,} | {d['clicks']:>7,} | {ctr:>4.1f}% | {d['installs']:>8} | {d['regs']:>4} | Rs {cpi:>6,.0f}{flag}")

print()
print("=== SUMMARY ===")
dates = sorted(daily_best.keys())
print(f"Data from: {dates[0]} to {dates[-1]} ({len(dates)} days)")

total_spend = sum(d["spend"] for d in daily_best.values())
total_installs = sum(d["installs"] for d in daily_best.values())
total_regs = sum(d["regs"] for d in daily_best.values())
avg_cpi = total_spend / total_installs if total_installs > 0 else 0

print(f"Total Spend: Rs {total_spend:,.0f}")
print(f"Total Installs: {total_installs}")
print(f"Total Registrations: {total_regs}")
print(f"Overall CPI: Rs {avg_cpi:,.0f}")

conn.close()
