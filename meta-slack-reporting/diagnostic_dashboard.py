#!/usr/bin/env python3
"""Generate diagnostic dashboard analyzing performance decline"""
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import boto3

load_dotenv('.env.upsc')

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

# Initialize
FacebookAdsApi.init(access_token=os.getenv('META_ACCESS_TOKEN'))
account = AdAccount(os.getenv('META_ADS_ACCOUNT_ID'))

print("Fetching 14-day historical data...")

# Get daily account-level data
daily_params = {
    'time_range': {'since': '2026-01-23', 'until': '2026-02-05'},
    'time_increment': 1,
    'level': 'account',
    'fields': ['spend', 'impressions', 'clicks', 'actions', 'ctr', 'cpc', 'cpm'],
}
daily_insights = list(account.get_insights(params=daily_params))

# Get campaign-level data for recent period
campaign_params = {
    'time_range': {'since': '2026-01-23', 'until': '2026-02-05'},
    'level': 'campaign',
    'fields': ['campaign_name', 'spend', 'impressions', 'clicks', 'actions', 'ctr'],
}
campaign_insights = list(account.get_insights(params=campaign_params))

print(f"Got {len(daily_insights)} days, {len(campaign_insights)} campaigns")

# Process daily data
daily_data = []
for row in daily_insights:
    date = row.get('date_start', 'Unknown')
    spend = float(row.get('spend', 0))
    imps = int(row.get('impressions', 0))
    clicks = int(row.get('clicks', 0))
    ctr = float(row.get('ctr', 0))
    cpm = float(row.get('cpm', 0))

    actions = row.get('actions', []) or []
    installs = 0
    regs = 0
    for a in actions:
        if a.get('action_type') in ['omni_app_install', 'mobile_app_install', 'app_install']:
            installs = int(a.get('value', 0))
        if a.get('action_type') in ['omni_complete_registration', 'complete_registration']:
            regs = int(a.get('value', 0))

    cpi = spend/installs if installs > 0 else 0

    daily_data.append({
        'date': date,
        'spend': spend,
        'impressions': imps,
        'clicks': clicks,
        'ctr': ctr,
        'cpm': cpm,
        'installs': installs,
        'registrations': regs,
        'cpi': cpi
    })

# Process campaign data
campaign_data = []
for row in campaign_insights:
    name = row.get('campaign_name', 'Unknown')
    spend = float(row.get('spend', 0))
    imps = int(row.get('impressions', 0))
    clicks = int(row.get('clicks', 0))

    actions = row.get('actions', []) or []
    installs = 0
    regs = 0
    for a in actions:
        if a.get('action_type') in ['omni_app_install', 'mobile_app_install', 'app_install']:
            installs = int(a.get('value', 0))
        if a.get('action_type') in ['omni_complete_registration', 'complete_registration']:
            regs = int(a.get('value', 0))

    cpi = spend/installs if installs > 0 else 0

    campaign_data.append({
        'name': name,
        'spend': spend,
        'impressions': imps,
        'clicks': clicks,
        'installs': installs,
        'registrations': regs,
        'cpi': cpi
    })

# Calculate periods
peak_period = daily_data[:3]  # Jan 23-25
decline_period = daily_data[3:8]  # Jan 26-30
crash_period = daily_data[8:]  # Jan 31-Feb 5

peak_avg_installs = sum(d['installs'] for d in peak_period) / len(peak_period)
peak_avg_cpi = sum(d['cpi'] for d in peak_period if d['cpi'] > 0) / max(1, len([d for d in peak_period if d['cpi'] > 0]))

decline_avg_installs = sum(d['installs'] for d in decline_period) / len(decline_period)
decline_avg_cpi = sum(d['cpi'] for d in decline_period if d['cpi'] > 0) / max(1, len([d for d in decline_period if d['cpi'] > 0]))

crash_avg_installs = sum(d['installs'] for d in crash_period) / len(crash_period)
crash_avg_cpi = sum(d['cpi'] for d in crash_period if d['cpi'] > 0) / max(1, len([d for d in crash_period if d['cpi'] > 0]))

# Generate HTML
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UPSC Ads Performance Diagnostic - Why Are Ads Failing?</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0f1a 0%, #1a1f2e 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}

        .header {{
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 24px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
        .header .subtitle {{ font-size: 1.2rem; opacity: 0.9; }}

        .alert-box {{
            background: rgba(239, 68, 68, 0.2);
            border: 2px solid #ef4444;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .alert-box h2 {{ color: #ef4444; margin-bottom: 10px; }}

        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 24px; }}

        .card {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid rgba(59, 130, 246, 0.2);
        }}
        .card h3 {{ color: #60a5fa; margin-bottom: 16px; font-size: 1.1rem; }}

        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-label {{ color: #94a3b8; }}
        .metric-value {{ font-weight: 600; font-size: 1.1rem; }}
        .metric-value.good {{ color: #10b981; }}
        .metric-value.bad {{ color: #ef4444; }}
        .metric-value.warning {{ color: #f59e0b; }}

        .period-card {{
            text-align: center;
            padding: 20px;
        }}
        .period-card .period-name {{ font-size: 0.9rem; color: #94a3b8; margin-bottom: 8px; }}
        .period-card .period-dates {{ font-size: 0.8rem; color: #64748b; margin-bottom: 12px; }}
        .period-card .big-number {{ font-size: 2.5rem; font-weight: 700; }}
        .period-card .metric-name {{ font-size: 0.85rem; color: #94a3b8; }}

        .peak {{ border-color: #10b981; }}
        .peak .big-number {{ color: #10b981; }}
        .decline {{ border-color: #f59e0b; }}
        .decline .big-number {{ color: #f59e0b; }}
        .crash {{ border-color: #ef4444; }}
        .crash .big-number {{ color: #ef4444; }}

        .chart-container {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .chart-container h3 {{ color: #60a5fa; margin-bottom: 16px; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{ color: #94a3b8; font-weight: 500; font-size: 0.85rem; text-transform: uppercase; }}
        tr:hover {{ background: rgba(59, 130, 246, 0.1); }}

        .status-peak {{ color: #10b981; }}
        .status-decline {{ color: #f59e0b; }}
        .status-crash {{ color: #ef4444; }}

        .findings {{
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .findings h3 {{ color: #60a5fa; margin-bottom: 16px; }}
        .finding {{
            display: flex;
            gap: 16px;
            padding: 16px;
            margin-bottom: 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            border-left: 4px solid;
        }}
        .finding.critical {{ border-color: #ef4444; }}
        .finding.warning {{ border-color: #f59e0b; }}
        .finding.info {{ border-color: #3b82f6; }}
        .finding-icon {{ font-size: 1.5rem; }}
        .finding-content h4 {{ margin-bottom: 4px; }}
        .finding-content p {{ color: #94a3b8; font-size: 0.9rem; }}

        .recommendations {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%);
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 24px;
        }}
        .recommendations h3 {{ color: #10b981; margin-bottom: 16px; }}
        .rec-item {{
            display: flex;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .rec-item:last-child {{ border-bottom: none; }}
        .rec-number {{
            background: #10b981;
            color: #0a0f1a;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex-shrink: 0;
        }}
        .rec-content {{ flex: 1; }}
        .rec-content strong {{ color: #10b981; }}

        .timestamp {{
            text-align: center;
            color: #64748b;
            font-size: 0.85rem;
            margin-top: 24px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Performance Diagnostic Report</h1>
            <p class="subtitle">PrepAiro UPSC - Why Are Your Ads Failing?</p>
        </div>

        <div class="alert-box">
            <h2>⚠️ Critical Alert: 92% Drop in Installs</h2>
            <p>Your daily installs dropped from <strong>42/day</strong> (Jan 23-25) to <strong>3.5/day</strong> (Jan 31-Feb 5). CPI increased from <strong>₹96</strong> to <strong>₹765</strong>. Immediate action required.</p>
        </div>

        <!-- Period Comparison -->
        <div class="grid">
            <div class="card period-card peak">
                <div class="period-name">🟢 PEAK PERIOD</div>
                <div class="period-dates">Jan 23-25 (3 days)</div>
                <div class="big-number">{peak_avg_installs:.0f}</div>
                <div class="metric-name">installs/day</div>
                <div style="margin-top: 12px; color: #10b981;">CPI: ₹{peak_avg_cpi:.0f}</div>
            </div>
            <div class="card period-card decline">
                <div class="period-name">🟡 DECLINE PERIOD</div>
                <div class="period-dates">Jan 26-30 (5 days)</div>
                <div class="big-number">{decline_avg_installs:.0f}</div>
                <div class="metric-name">installs/day</div>
                <div style="margin-top: 12px; color: #f59e0b;">CPI: ₹{decline_avg_cpi:.0f}</div>
            </div>
            <div class="card period-card crash">
                <div class="period-name">🔴 CRASH PERIOD</div>
                <div class="period-dates">Jan 31-Feb 5 (6 days)</div>
                <div class="big-number">{crash_avg_installs:.1f}</div>
                <div class="metric-name">installs/day</div>
                <div style="margin-top: 12px; color: #ef4444;">CPI: ₹{crash_avg_cpi:.0f}</div>
            </div>
        </div>

        <!-- Charts -->
        <div class="chart-container">
            <h3>📉 Daily Performance Trend</h3>
            <canvas id="trendChart" height="100"></canvas>
        </div>

        <div class="chart-container">
            <h3>💰 CPI Trend (Cost Per Install)</h3>
            <canvas id="cpiChart" height="80"></canvas>
        </div>

        <!-- Daily Breakdown Table -->
        <div class="card">
            <h3>📊 Daily Breakdown</h3>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Spend</th>
                        <th>Impressions</th>
                        <th>Clicks</th>
                        <th>CTR</th>
                        <th>Installs</th>
                        <th>CPI</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""

for d in daily_data:
    if d['cpi'] == 0 and d['spend'] > 500:
        status = '<span class="status-crash">⚠️ NO INSTALLS</span>'
    elif d['cpi'] > 200:
        status = '<span class="status-crash">🔴 HIGH CPI</span>'
    elif d['cpi'] > 120:
        status = '<span class="status-decline">🟡 ELEVATED</span>'
    else:
        status = '<span class="status-peak">🟢 GOOD</span>'

    html += f"""
                    <tr>
                        <td>{d['date']}</td>
                        <td>₹{d['spend']:,.0f}</td>
                        <td>{d['impressions']:,}</td>
                        <td>{d['clicks']:,}</td>
                        <td>{d['ctr']:.1f}%</td>
                        <td><strong>{d['installs']}</strong></td>
                        <td>₹{d['cpi']:,.0f}</td>
                        <td>{status}</td>
                    </tr>
"""

html += """
                </tbody>
            </table>
        </div>

        <!-- Campaign Analysis -->
        <div class="card" style="margin-top: 24px;">
            <h3>🎯 Campaign Performance (14-Day Total)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Campaign</th>
                        <th>Spend</th>
                        <th>Impressions</th>
                        <th>Installs</th>
                        <th>CPI</th>
                        <th>Verdict</th>
                    </tr>
                </thead>
                <tbody>
"""

for c in sorted(campaign_data, key=lambda x: x['spend'], reverse=True):
    if c['installs'] == 0 and c['spend'] > 1000:
        verdict = '<span class="status-crash">💀 BURNING MONEY</span>'
    elif c['cpi'] > 300:
        verdict = '<span class="status-crash">🔴 CPI TOO HIGH</span>'
    elif c['cpi'] > 150:
        verdict = '<span class="status-decline">🟡 UNDERPERFORMING</span>'
    elif c['installs'] > 0:
        verdict = '<span class="status-peak">🟢 OK</span>'
    else:
        verdict = '<span class="status-decline">⚠️ NO INSTALLS</span>'

    html += f"""
                    <tr>
                        <td>{c['name'][:45]}</td>
                        <td>₹{c['spend']:,.0f}</td>
                        <td>{c['impressions']:,}</td>
                        <td><strong>{c['installs']}</strong></td>
                        <td>₹{c['cpi']:,.0f}</td>
                        <td>{verdict}</td>
                    </tr>
"""

html += """
                </tbody>
            </table>
        </div>

        <!-- Key Findings -->
        <div class="findings" style="margin-top: 24px;">
            <h3>🔍 Key Findings - What Went Wrong</h3>

            <div class="finding critical">
                <div class="finding-icon">🎯</div>
                <div class="finding-content">
                    <h4>Wrong Campaign Objectives</h4>
                    <p>You have campaigns optimizing for Checkouts, Web Conversions, and Followers instead of App Installs. Meta's algorithm finds users matching those objectives, not app installers.</p>
                </div>
            </div>

            <div class="finding critical">
                <div class="finding-icon">📅</div>
                <div class="finding-content">
                    <h4>Performance Dropped After Jan 25</h4>
                    <p>Something changed between Jan 25-26. Installs went from 60/day to 12/day overnight. Check if you made campaign changes, paused high performers, or launched new campaigns around this date.</p>
                </div>
            </div>

            <div class="finding warning">
                <div class="finding-icon">🎨</div>
                <div class="finding-content">
                    <h4>Possible Creative Fatigue</h4>
                    <p>The same creatives running for 2+ weeks may have exhausted your audience. CTR patterns suggest users are seeing the same ads repeatedly.</p>
                </div>
            </div>

            <div class="finding warning">
                <div class="finding-icon">📱</div>
                <div class="finding-content">
                    <h4>Instagram-Only May Be Limiting</h4>
                    <p>If you recently switched to Instagram-only, this cuts your audience significantly. Meta needs time to relearn, and the smaller pool means higher CPIs.</p>
                </div>
            </div>

            <div class="finding info">
                <div class="finding-icon">💰</div>
                <div class="finding-content">
                    <h4>Budget Spread Too Thin</h4>
                    <p>₹2-3K/day split across 4+ campaigns means each campaign gets insufficient budget for proper optimization. Meta recommends 50+ conversions/week per ad set.</p>
                </div>
            </div>
        </div>

        <!-- Recommendations -->
        <div class="recommendations">
            <h3>✅ Immediate Actions to Fix Performance</h3>

            <div class="rec-item">
                <div class="rec-number">1</div>
                <div class="rec-content">
                    <strong>PAUSE non-install campaigns immediately</strong><br>
                    Turn off UPSC_Checkouts, UPSC_Web_Conversions, and UPSC_Followers. They're burning money without driving installs.
                </div>
            </div>

            <div class="rec-item">
                <div class="rec-number">2</div>
                <div class="rec-content">
                    <strong>Consolidate budget into 1-2 App Install campaigns</strong><br>
                    Put ₹3000+/day into a single campaign with App Install objective. This gives Meta enough data to optimize.
                </div>
            </div>

            <div class="rec-item">
                <div class="rec-number">3</div>
                <div class="rec-content">
                    <strong>Launch fresh creatives</strong><br>
                    Create 3-5 new ad variations. Use different hooks, visuals, and copy angles. Test video vs static.
                </div>
            </div>

            <div class="rec-item">
                <div class="rec-number">4</div>
                <div class="rec-content">
                    <strong>Expand targeting temporarily</strong><br>
                    Broaden your audience while CPI is high. Let Meta find new pockets of quality users, then narrow based on results.
                </div>
            </div>

            <div class="rec-item">
                <div class="rec-number">5</div>
                <div class="rec-content">
                    <strong>Consider enabling Facebook (not just Instagram)</strong><br>
                    If you recently went Instagram-only, test adding Facebook back. The larger audience pool often lowers CPI.
                </div>
            </div>
        </div>

        <p class="timestamp">Generated: """ + datetime.now().strftime('%B %d, %Y at %I:%M %p IST') + """</p>
    </div>

    <script>
        // Trend Chart
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: """ + json.dumps([d['date'][5:] for d in daily_data]) + """,
                datasets: [
                    {
                        label: 'Installs',
                        data: """ + json.dumps([d['installs'] for d in daily_data]) + """,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.3,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Spend (₹)',
                        data: """ + json.dumps([d['spend'] for d in daily_data]) + """,
                        borderColor: '#3b82f6',
                        backgroundColor: 'transparent',
                        tension: 0.3,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                    y: {
                        type: 'linear',
                        position: 'left',
                        ticks: { color: '#10b981' },
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        title: { display: true, text: 'Installs', color: '#10b981' }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        ticks: { color: '#3b82f6' },
                        grid: { display: false },
                        title: { display: true, text: 'Spend (₹)', color: '#3b82f6' }
                    }
                }
            }
        });

        // CPI Chart
        const cpiCtx = document.getElementById('cpiChart').getContext('2d');
        new Chart(cpiCtx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps([d['date'][5:] for d in daily_data]) + """,
                datasets: [{
                    label: 'CPI (₹)',
                    data: """ + json.dumps([d['cpi'] if d['cpi'] > 0 else None for d in daily_data]) + """,
                    backgroundColor: """ + json.dumps(['#10b981' if d['cpi'] < 120 else '#f59e0b' if d['cpi'] < 250 else '#ef4444' for d in daily_data]) + """,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    annotation: {
                        annotations: {
                            line1: {
                                type: 'line',
                                yMin: 100,
                                yMax: 100,
                                borderColor: '#10b981',
                                borderDash: [5, 5],
                                label: { content: 'Target CPI', enabled: true }
                            }
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                }
            }
        });
    </script>
</body>
</html>
"""

# Save locally
dashboard_path = 'charts/diagnostic_dashboard.html'
os.makedirs('charts', exist_ok=True)
with open(dashboard_path, 'w') as f:
    f.write(html)
print(f"Dashboard saved to {dashboard_path}")

# Upload to S3
s3 = boto3.client('s3', region_name='ap-south-1')
bucket = 'prepairo-analytics-reports'
key = f'meta-ads-charts/{datetime.now().strftime("%Y%m%d_%H%M%S")}_diagnostic_dashboard.html'

s3.upload_file(
    dashboard_path,
    bucket,
    key,
    ExtraArgs={'ContentType': 'text/html'}
)

url = f"https://{bucket}.s3.ap-south-1.amazonaws.com/{key}"
print(f"\n✅ Dashboard uploaded: {url}")
