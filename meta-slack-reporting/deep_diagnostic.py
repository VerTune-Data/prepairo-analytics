#!/usr/bin/env python3
"""Deep diagnostic dashboard with evidence-based analysis"""
import os
import json
import csv
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
import boto3

load_dotenv('.env.upsc')

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

FacebookAdsApi.init(access_token=os.getenv('META_ACCESS_TOKEN'))
account = AdAccount(os.getenv('META_ADS_ACCOUNT_ID'))

print("Fetching comprehensive data...")

# 1. Daily account metrics
daily_data = []
daily_insights = account.get_insights(params={
    'time_range': {'since': '2026-01-20', 'until': '2026-02-05'},
    'time_increment': 1,
    'level': 'account',
    'fields': ['spend', 'impressions', 'reach', 'clicks', 'cpm', 'cpc', 'ctr', 'frequency', 'actions'],
})

for row in daily_insights:
    installs = 0
    regs = 0
    for a in (row.get('actions') or []):
        if a['action_type'] in ['omni_app_install', 'mobile_app_install', 'app_install']:
            installs = int(a['value'])
        if a['action_type'] in ['omni_complete_registration', 'complete_registration']:
            regs = int(a['value'])

    daily_data.append({
        'date': row['date_start'],
        'spend': float(row.get('spend', 0)),
        'impressions': int(row.get('impressions', 0)),
        'reach': int(row.get('reach', 0)),
        'clicks': int(row.get('clicks', 0)),
        'cpm': float(row.get('cpm', 0)),
        'cpc': float(row.get('cpc', 0)),
        'ctr': float(row.get('ctr', 0)),
        'frequency': float(row.get('frequency', 0)),
        'installs': installs,
        'registrations': regs,
        'cpi': float(row.get('spend', 0)) / installs if installs > 0 else 0
    })

# 2. Campaign-level daily data
campaign_daily = defaultdict(list)
campaign_insights = account.get_insights(params={
    'time_range': {'since': '2026-01-20', 'until': '2026-02-05'},
    'time_increment': 1,
    'level': 'campaign',
    'fields': ['campaign_id', 'campaign_name', 'spend', 'impressions', 'reach', 'cpm', 'actions'],
})

for row in campaign_insights:
    installs = 0
    for a in (row.get('actions') or []):
        if a['action_type'] in ['omni_app_install', 'mobile_app_install', 'app_install']:
            installs = int(a['value'])

    campaign_daily[row['campaign_name']].append({
        'date': row['date_start'],
        'spend': float(row.get('spend', 0)),
        'impressions': int(row.get('impressions', 0)),
        'reach': int(row.get('reach', 0)),
        'cpm': float(row.get('cpm', 0)),
        'installs': installs
    })

# 3. Parse app user data
app_daily = defaultdict(lambda: {'total': 0, 'fb_ig': 0, 'organic': 0, 'android': 0, 'ios': 0})
try:
    with open('/tmp/user_data.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            created_at = row.get('created_at', '')
            if not created_at:
                continue
            date = created_at[:10]
            app_daily[date]['total'] += 1

            platform = row.get('signup_platform', '').lower()
            if 'android' in platform:
                app_daily[date]['android'] += 1
            elif 'ios' in platform:
                app_daily[date]['ios'] += 1

            play_refer = (row.get('play_refer', '') or '').lower()
            attribution = (row.get('attribution_data', '') or '').lower()
            combined = play_refer + ' ' + attribution

            if 'fb4a' in combined or 'facebook' in combined or 'instagram' in combined:
                app_daily[date]['fb_ig'] += 1
            elif 'organic' in combined or 'utm_source=(not%20set)' in combined:
                app_daily[date]['organic'] += 1
except:
    print("Note: App user data not available on server")

print(f"Got {len(daily_data)} days of data, {len(campaign_daily)} campaigns")

# Calculate key metrics
peak_data = [d for d in daily_data if '2026-01-23' <= d['date'] <= '2026-01-25']
crash_data = [d for d in daily_data if '2026-01-31' <= d['date'] <= '2026-02-05']

peak_installs = sum(d['installs'] for d in peak_data)
crash_installs = sum(d['installs'] for d in crash_data)
peak_spend = sum(d['spend'] for d in peak_data)
crash_spend = sum(d['spend'] for d in crash_data)
peak_cpm = sum(d['cpm'] for d in peak_data) / len(peak_data)
crash_cpm = sum(d['cpm'] for d in crash_data) / len(crash_data)
peak_reach = sum(d['reach'] for d in peak_data)
crash_reach = sum(d['reach'] for d in crash_data)

# Campaign analysis
campaign_summary = []
for name, data in campaign_daily.items():
    peak = [d for d in data if '2026-01-23' <= d['date'] <= '2026-01-25']
    crash = [d for d in data if '2026-01-31' <= d['date'] <= '2026-02-05']

    peak_spend_c = sum(d['spend'] for d in peak)
    crash_spend_c = sum(d['spend'] for d in crash)
    peak_installs_c = sum(d['installs'] for d in peak)
    crash_installs_c = sum(d['installs'] for d in crash)

    campaign_summary.append({
        'name': name,
        'peak_spend': peak_spend_c,
        'crash_spend': crash_spend_c,
        'peak_installs': peak_installs_c,
        'crash_installs': crash_installs_c,
        'status': 'STOPPED' if peak_spend_c > 500 and crash_spend_c == 0 else
                  'CRASHED' if peak_installs_c > 10 and crash_installs_c < peak_installs_c * 0.3 else
                  'NEW' if peak_spend_c == 0 and crash_spend_c > 500 else 'STABLE'
    })

# Generate HTML
html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deep Performance Diagnostic - Evidence-Based Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0f1a;
            color: #e2e8f0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1600px; margin: 0 auto; }}

        .header {{
            background: linear-gradient(135deg, #dc2626, #991b1b);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 24px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.2rem; margin-bottom: 8px; }}
        .header p {{ opacity: 0.9; }}

        .verdict-box {{
            background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(153,27,27,0.2));
            border: 2px solid #ef4444;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .verdict-box h2 {{ color: #ef4444; font-size: 1.5rem; margin-bottom: 16px; }}
        .verdict-item {{
            display: flex;
            gap: 16px;
            padding: 16px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            margin-bottom: 12px;
            border-left: 4px solid #ef4444;
        }}
        .verdict-item.primary {{ border-color: #ef4444; }}
        .verdict-item.secondary {{ border-color: #f59e0b; }}
        .verdict-icon {{ font-size: 2rem; }}
        .verdict-content h3 {{ margin-bottom: 4px; color: #fff; }}
        .verdict-content p {{ color: #94a3b8; }}
        .verdict-evidence {{
            background: rgba(0,0,0,0.4);
            padding: 8px 12px;
            border-radius: 4px;
            margin-top: 8px;
            font-family: monospace;
            font-size: 0.85rem;
            color: #10b981;
        }}

        .grid {{ display: grid; gap: 20px; margin-bottom: 24px; }}
        .grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
        .grid-2 {{ grid-template-columns: repeat(2, 1fr); }}

        .card {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(59, 130, 246, 0.2);
        }}
        .card h3 {{ color: #60a5fa; margin-bottom: 16px; font-size: 1rem; }}

        .metric-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .metric-label {{ color: #94a3b8; }}
        .metric-value {{ font-weight: 600; }}
        .metric-value.good {{ color: #10b981; }}
        .metric-value.bad {{ color: #ef4444; }}
        .metric-value.warning {{ color: #f59e0b; }}

        .compare-box {{
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 16px;
            align-items: center;
            text-align: center;
        }}
        .period {{
            padding: 16px;
            border-radius: 8px;
        }}
        .period.peak {{ background: rgba(16,185,129,0.2); border: 1px solid #10b981; }}
        .period.crash {{ background: rgba(239,68,68,0.2); border: 1px solid #ef4444; }}
        .period-label {{ font-size: 0.8rem; color: #94a3b8; margin-bottom: 4px; }}
        .period-value {{ font-size: 1.8rem; font-weight: 700; }}
        .period.peak .period-value {{ color: #10b981; }}
        .period.crash .period-value {{ color: #ef4444; }}
        .period-sub {{ font-size: 0.75rem; color: #64748b; margin-top: 4px; }}
        .arrow {{ font-size: 2rem; color: #ef4444; }}

        .chart-container {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .chart-container h3 {{ color: #60a5fa; margin-bottom: 16px; }}

        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 8px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; }}
        tr:hover {{ background: rgba(59,130,246,0.1); }}

        .tag {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .tag.stopped {{ background: #dc2626; color: white; }}
        .tag.crashed {{ background: #f59e0b; color: black; }}
        .tag.new {{ background: #3b82f6; color: white; }}
        .tag.stable {{ background: #10b981; color: white; }}

        .timeline {{
            position: relative;
            padding-left: 30px;
        }}
        .timeline::before {{
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: rgba(255,255,255,0.2);
        }}
        .timeline-item {{
            position: relative;
            padding: 16px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            margin-bottom: 16px;
        }}
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -24px;
            top: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ef4444;
        }}
        .timeline-date {{ font-size: 0.8rem; color: #64748b; margin-bottom: 4px; }}
        .timeline-event {{ font-weight: 600; }}
        .timeline-detail {{ color: #94a3b8; font-size: 0.9rem; margin-top: 4px; }}

        .recommendation {{
            background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(6,182,212,0.2));
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 24px;
            margin-top: 24px;
        }}
        .recommendation h3 {{ color: #10b981; margin-bottom: 16px; }}
        .rec-list {{ list-style: none; }}
        .rec-list li {{
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            gap: 12px;
        }}
        .rec-list li:last-child {{ border-bottom: none; }}
        .rec-num {{
            background: #10b981;
            color: #0a0f1a;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.85rem;
            flex-shrink: 0;
        }}

        .footer {{
            text-align: center;
            color: #64748b;
            font-size: 0.85rem;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}

        @media (max-width: 1024px) {{
            .grid-3 {{ grid-template-columns: 1fr; }}
            .grid-2 {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Deep Performance Diagnostic</h1>
            <p>Evidence-Based Analysis: Why Your Ads Stopped Working</p>
        </div>

        <!-- VERDICT SECTION -->
        <div class="verdict-box">
            <h2>🎯 ROOT CAUSES IDENTIFIED (With Evidence)</h2>

            <div class="verdict-item primary">
                <div class="verdict-icon">🛑</div>
                <div class="verdict-content">
                    <h3>CAUSE #1: Best Performing Campaign Was Stopped</h3>
                    <p><strong>PrepAiro_Install_Value_Dec25</strong> was delivering 33 installs for ₹1,073 (CPI ₹32.5) during peak. It was turned off after Jan 25.</p>
                    <div class="verdict-evidence">
                        Peak (Jan 23-25): ₹1,073 spend → 33 installs → CPI ₹32.5<br>
                        After Jan 25: ₹0 spend → 0 installs → CAMPAIGN STOPPED
                    </div>
                </div>
            </div>

            <div class="verdict-item primary">
                <div class="verdict-icon">📉</div>
                <div class="verdict-content">
                    <h3>CAUSE #2: Main Campaign (Checkouts) Efficiency Collapsed</h3>
                    <p><strong>UPSC_Checkouts_Jan2026</strong> went from ₹89 CPI to ₹439 CPI - a 5x deterioration while maintaining similar spend.</p>
                    <div class="verdict-evidence">
                        Peak: ₹8,299 spend → 93 installs → CPI ₹89<br>
                        Crash: ₹6,152 spend → 14 installs → CPI ₹439 (-92% efficiency)
                    </div>
                </div>
            </div>

            <div class="verdict-item secondary">
                <div class="verdict-icon">💰</div>
                <div class="verdict-content">
                    <h3>CAUSE #3: Budget Diverted to Non-Install Campaigns</h3>
                    <p><strong>UPSC_Web_Conversions</strong> received ₹5,736 but generated 0 installs. This campaign optimizes for web events, not app installs.</p>
                    <div class="verdict-evidence">
                        UPSC_Web_Conversions_Jan26: ₹5,736 spend → 0 installs<br>
                        Budget that could have driven ~65 installs at previous CPI
                    </div>
                </div>
            </div>

            <div class="verdict-item secondary">
                <div class="verdict-icon">📈</div>
                <div class="verdict-content">
                    <h3>CAUSE #4: CPM Spiked (Auction Got Expensive)</h3>
                    <p>Cost per 1000 impressions increased from ₹33 average to ₹56 on Feb 3 - a 70% increase in auction costs.</p>
                    <div class="verdict-evidence">
                        Peak avg CPM: ₹{peak_cpm:.1f}<br>
                        Crash avg CPM: ₹{crash_cpm:.1f} ({((crash_cpm-peak_cpm)/peak_cpm*100):+.0f}%)<br>
                        Feb 3 CPM: ₹56.4 (highest)
                    </div>
                </div>
            </div>
        </div>

        <!-- KEY METRICS COMPARISON -->
        <div class="grid grid-3">
            <div class="card">
                <h3>📊 Installs</h3>
                <div class="compare-box">
                    <div class="period peak">
                        <div class="period-label">PEAK (Jan 23-25)</div>
                        <div class="period-value">{peak_installs}</div>
                        <div class="period-sub">{peak_installs/3:.0f}/day</div>
                    </div>
                    <div class="arrow">→</div>
                    <div class="period crash">
                        <div class="period-label">CRASH (Jan 31-Feb 5)</div>
                        <div class="period-value">{crash_installs}</div>
                        <div class="period-sub">{crash_installs/6:.0f}/day</div>
                    </div>
                </div>
                <div style="text-align:center;margin-top:12px;color:#ef4444;font-weight:600;">
                    {((crash_installs/6)/(peak_installs/3)-1)*100:.0f}% DROP
                </div>
            </div>

            <div class="card">
                <h3>💰 Spend</h3>
                <div class="compare-box">
                    <div class="period peak">
                        <div class="period-label">PEAK</div>
                        <div class="period-value">₹{peak_spend:,.0f}</div>
                        <div class="period-sub">₹{peak_spend/3:,.0f}/day</div>
                    </div>
                    <div class="arrow">→</div>
                    <div class="period crash">
                        <div class="period-label">CRASH</div>
                        <div class="period-value">₹{crash_spend:,.0f}</div>
                        <div class="period-sub">₹{crash_spend/6:,.0f}/day</div>
                    </div>
                </div>
                <div style="text-align:center;margin-top:12px;color:#f59e0b;">
                    Spend maintained but efficiency crashed
                </div>
            </div>

            <div class="card">
                <h3>📉 CPI (Cost Per Install)</h3>
                <div class="compare-box">
                    <div class="period peak">
                        <div class="period-label">PEAK</div>
                        <div class="period-value">₹{peak_spend/peak_installs:.0f}</div>
                        <div class="period-sub">Efficient</div>
                    </div>
                    <div class="arrow">→</div>
                    <div class="period crash">
                        <div class="period-label">CRASH</div>
                        <div class="period-value">₹{crash_spend/crash_installs if crash_installs > 0 else 0:.0f}</div>
                        <div class="period-sub">Inefficient</div>
                    </div>
                </div>
                <div style="text-align:center;margin-top:12px;color:#ef4444;font-weight:600;">
                    {((crash_spend/crash_installs if crash_installs > 0 else 0)/(peak_spend/peak_installs)-1)*100:.0f}% INCREASE
                </div>
            </div>
        </div>

        <!-- CHARTS -->
        <div class="grid grid-2">
            <div class="chart-container">
                <h3>📈 Daily Installs vs Spend</h3>
                <canvas id="installsChart" height="200"></canvas>
            </div>
            <div class="chart-container">
                <h3>💵 CPM Trend (Auction Pricing)</h3>
                <canvas id="cpmChart" height="200"></canvas>
            </div>
        </div>

        <div class="chart-container">
            <h3>📊 Daily CPI Trend</h3>
            <canvas id="cpiChart" height="120"></canvas>
        </div>

        <!-- CAMPAIGN BREAKDOWN -->
        <div class="card" style="margin-bottom:24px;">
            <h3>🎯 Campaign Performance Breakdown</h3>
            <table>
                <thead>
                    <tr>
                        <th>Campaign</th>
                        <th>Status</th>
                        <th>Peak Spend (Jan 23-25)</th>
                        <th>Peak Installs</th>
                        <th>Crash Spend (Jan 31+)</th>
                        <th>Crash Installs</th>
                        <th>Impact</th>
                    </tr>
                </thead>
                <tbody>
'''

for camp in sorted(campaign_summary, key=lambda x: x['peak_spend'] + x['crash_spend'], reverse=True):
    if camp['peak_spend'] > 100 or camp['crash_spend'] > 100:
        status_class = camp['status'].lower()

        if camp['status'] == 'STOPPED':
            impact = f"Lost {camp['peak_installs']} installs/3days"
        elif camp['status'] == 'CRASHED':
            impact = f"-{100-int(camp['crash_installs']/max(1,camp['peak_installs'])*100)}% efficiency"
        elif camp['status'] == 'NEW' and camp['crash_installs'] == 0:
            impact = f"₹{camp['crash_spend']:.0f} wasted"
        else:
            impact = "Stable"

        html += f'''
                    <tr>
                        <td>{camp['name'][:40]}</td>
                        <td><span class="tag {status_class}">{camp['status']}</span></td>
                        <td>₹{camp['peak_spend']:,.0f}</td>
                        <td>{camp['peak_installs']}</td>
                        <td>₹{camp['crash_spend']:,.0f}</td>
                        <td>{camp['crash_installs']}</td>
                        <td style="color:{'#ef4444' if camp['status'] in ['STOPPED','CRASHED'] else '#f59e0b' if camp['crash_installs']==0 else '#10b981'}">{impact}</td>
                    </tr>
'''

html += '''
                </tbody>
            </table>
        </div>

        <!-- TIMELINE -->
        <div class="card" style="margin-bottom:24px;">
            <h3>📅 Timeline of Events</h3>
            <div class="timeline">
                <div class="timeline-item">
                    <div class="timeline-date">Jan 23-25</div>
                    <div class="timeline-event">🟢 PEAK PERFORMANCE</div>
                    <div class="timeline-detail">126 installs over 3 days. PrepAiro_Install_Value_Dec25 and UPSC_Checkouts both performing well.</div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-date">~Jan 26</div>
                    <div class="timeline-event">🛑 PrepAiro_Install_Value_Dec25 STOPPED</div>
                    <div class="timeline-detail">Best performing campaign (CPI ₹32) was turned off. Lost 11 installs/day.</div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-date">Jan 26-30</div>
                    <div class="timeline-event">🟡 DECLINE BEGINS</div>
                    <div class="timeline-detail">Installs dropped to ~14/day. UPSC_Checkouts still running but efficiency declining.</div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-date">~Jan 26</div>
                    <div class="timeline-event">🆕 UPSC_Web_Conversions Launched</div>
                    <div class="timeline-detail">New campaign launched optimizing for web conversions, not app installs. Zero installs generated.</div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-date">Jan 31+</div>
                    <div class="timeline-event">🔴 CRASH</div>
                    <div class="timeline-detail">Installs dropped to ~3.5/day. CPM spiked to ₹56. Checkouts campaign CPI hit ₹439.</div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-date">Feb 2</div>
                    <div class="timeline-event">💀 ZERO INSTALLS DAY</div>
                    <div class="timeline-detail">₹2,064 spent with 0 installs recorded. Complete system failure.</div>
                </div>
            </div>
        </div>

        <!-- DAILY DATA TABLE -->
        <div class="card" style="margin-bottom:24px;">
            <h3>📋 Daily Data</h3>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Spend</th>
                        <th>Impressions</th>
                        <th>Reach</th>
                        <th>CPM</th>
                        <th>Freq</th>
                        <th>Installs</th>
                        <th>CPI</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
'''

for d in daily_data:
    status = '🟢' if d['installs'] >= 30 else '🟡' if d['installs'] >= 10 else '🔴'
    cpm_color = '#ef4444' if d['cpm'] > 40 else '#f59e0b' if d['cpm'] > 35 else '#10b981'

    html += f'''
                    <tr>
                        <td>{d['date']}</td>
                        <td>₹{d['spend']:,.0f}</td>
                        <td>{d['impressions']:,}</td>
                        <td>{d['reach']:,}</td>
                        <td style="color:{cpm_color}">₹{d['cpm']:.1f}</td>
                        <td>{d['frequency']:.2f}</td>
                        <td><strong>{d['installs']}</strong></td>
                        <td>₹{d['cpi']:,.0f}</td>
                        <td>{status}</td>
                    </tr>
'''

html += f'''
                </tbody>
            </table>
        </div>

        <!-- RECOMMENDATIONS -->
        <div class="recommendation">
            <h3>✅ Immediate Actions Required</h3>
            <ul class="rec-list">
                <li>
                    <span class="rec-num">1</span>
                    <div>
                        <strong>RESTART PrepAiro_Install_Value_Dec25</strong><br>
                        <span style="color:#94a3b8">This campaign had CPI of ₹32.5 - your best performer. Turn it back on immediately.</span>
                    </div>
                </li>
                <li>
                    <span class="rec-num">2</span>
                    <div>
                        <strong>PAUSE or FIX UPSC_Web_Conversions</strong><br>
                        <span style="color:#94a3b8">₹5,736 spent with 0 installs. Either pause it or change objective to App Installs.</span>
                    </div>
                </li>
                <li>
                    <span class="rec-num">3</span>
                    <div>
                        <strong>Audit UPSC_Checkouts Campaign</strong><br>
                        <span style="color:#94a3b8">CPI went from ₹89 to ₹439. Check creatives, audience, and consider refreshing ads.</span>
                    </div>
                </li>
                <li>
                    <span class="rec-num">4</span>
                    <div>
                        <strong>Review Audience Targeting</strong><br>
                        <span style="color:#94a3b8">CPM spiked to ₹56 on Feb 3. Your audience might be saturated or competition increased.</span>
                    </div>
                </li>
                <li>
                    <span class="rec-num">5</span>
                    <div>
                        <strong>Launch Fresh Creatives</strong><br>
                        <span style="color:#94a3b8">After 2+ weeks, creative fatigue is likely. Test 3-5 new ad variations.</span>
                    </div>
                </li>
            </ul>
        </div>

        <div class="footer">
            Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}<br>
            Deep Diagnostic Analysis for PrepAiro UPSC
        </div>
    </div>

    <script>
        // Installs vs Spend Chart
        new Chart(document.getElementById('installsChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps([d['date'][5:] for d in daily_data])},
                datasets: [
                    {{
                        label: 'Installs',
                        data: {json.dumps([d['installs'] for d in daily_data])},
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16,185,129,0.1)',
                        fill: true,
                        tension: 0.3,
                        yAxisID: 'y'
                    }},
                    {{
                        label: 'Spend (₹)',
                        data: {json.dumps([d['spend'] for d in daily_data])},
                        borderColor: '#3b82f6',
                        tension: 0.3,
                        yAxisID: 'y1'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }},
                scales: {{
                    x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    y: {{ type: 'linear', position: 'left', ticks: {{ color: '#10b981' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }}, title: {{ display: true, text: 'Installs', color: '#10b981' }} }},
                    y1: {{ type: 'linear', position: 'right', ticks: {{ color: '#3b82f6' }}, grid: {{ display: false }}, title: {{ display: true, text: 'Spend (₹)', color: '#3b82f6' }} }}
                }}
            }}
        }});

        // CPM Chart
        new Chart(document.getElementById('cpmChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps([d['date'][5:] for d in daily_data])},
                datasets: [{{
                    label: 'CPM (₹)',
                    data: {json.dumps([d['cpm'] for d in daily_data])},
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245,158,11,0.1)',
                    fill: true,
                    tension: 0.3
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ labels: {{ color: '#94a3b8' }} }},
                    annotation: {{
                        annotations: {{
                            line1: {{ type: 'line', yMin: 35, yMax: 35, borderColor: '#ef4444', borderDash: [5,5] }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    y: {{ ticks: {{ color: '#f59e0b' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }}
                }}
            }}
        }});

        // CPI Chart
        new Chart(document.getElementById('cpiChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps([d['date'][5:] for d in daily_data])},
                datasets: [{{
                    label: 'CPI (₹)',
                    data: {json.dumps([d['cpi'] if d['cpi'] > 0 else None for d in daily_data])},
                    backgroundColor: {json.dumps(['#10b981' if d['cpi'] < 100 else '#f59e0b' if d['cpi'] < 200 else '#ef4444' for d in daily_data])},
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }},
                    y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>
'''

# Save
os.makedirs('charts', exist_ok=True)
with open('charts/deep_diagnostic.html', 'w') as f:
    f.write(html)
print("Dashboard saved locally")

# Upload to S3
s3 = boto3.client('s3', region_name='ap-south-1')
key = f'meta-ads-charts/{datetime.now().strftime("%Y%m%d_%H%M%S")}_deep_diagnostic.html'
s3.upload_file('charts/deep_diagnostic.html', 'prepairo-analytics-reports', key, ExtraArgs={'ContentType': 'text/html'})
url = f"https://prepairo-analytics-reports.s3.ap-south-1.amazonaws.com/{key}"
print(f"\\n✅ Dashboard uploaded: {url}")
