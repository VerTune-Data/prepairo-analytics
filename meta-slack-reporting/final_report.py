#!/usr/bin/env python3
"""Final diagnostic report with recommendations"""
import os
from datetime import datetime
import boto3

html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meta Ads Performance Analysis - Final Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }

        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 { font-size: 2.2rem; margin-bottom: 8px; color: #fff; }
        .header .subtitle { color: #94a3b8; font-size: 1.1rem; }
        .header .date { color: #64748b; font-size: 0.9rem; margin-top: 12px; }

        .section {
            background: rgba(30, 41, 59, 0.6);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 24px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .section h2 {
            font-size: 1.3rem;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #3b82f6;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .alert {
            background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(185,28,28,0.15));
            border: 1px solid #ef4444;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
        }
        .alert h3 { color: #ef4444; margin-bottom: 8px; }
        .alert p { color: #fca5a5; }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin: 20px 0;
        }
        .metric-card {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .metric-card .label { color: #94a3b8; font-size: 0.85rem; margin-bottom: 8px; }
        .metric-card .value { font-size: 2rem; font-weight: 700; }
        .metric-card .change { font-size: 0.85rem; margin-top: 4px; }
        .metric-card.bad .value { color: #ef4444; }
        .metric-card.good .value { color: #10b981; }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }
        th, td {
            padding: 14px 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th { color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; }

        .cause-item {
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            border-left: 4px solid #ef4444;
        }
        .cause-item h4 { color: #fff; margin-bottom: 8px; font-size: 1.1rem; }
        .cause-item p { color: #94a3b8; margin-bottom: 12px; }
        .cause-item .evidence {
            background: rgba(0,0,0,0.3);
            padding: 12px;
            border-radius: 8px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.85rem;
            color: #10b981;
        }

        .timeline {
            position: relative;
            padding-left: 30px;
        }
        .timeline::before {
            content: '';
            position: absolute;
            left: 8px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, #10b981, #f59e0b, #ef4444);
        }
        .timeline-item {
            position: relative;
            padding: 16px 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            margin-bottom: 16px;
        }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -26px;
            top: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #fff;
        }
        .timeline-item.good::before { background: #10b981; }
        .timeline-item.warning::before { background: #f59e0b; }
        .timeline-item.bad::before { background: #ef4444; }
        .timeline-date { font-size: 0.8rem; color: #64748b; }
        .timeline-title { font-weight: 600; margin: 4px 0; }
        .timeline-desc { color: #94a3b8; font-size: 0.9rem; }

        .recommendation {
            background: linear-gradient(135deg, rgba(16,185,129,0.1), rgba(6,182,212,0.1));
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 12px;
            display: flex;
            gap: 16px;
        }
        .rec-priority {
            background: #10b981;
            color: #0f172a;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex-shrink: 0;
        }
        .rec-content h4 { color: #10b981; margin-bottom: 4px; }
        .rec-content p { color: #94a3b8; font-size: 0.9rem; }
        .rec-impact {
            margin-top: 8px;
            font-size: 0.85rem;
            color: #5eead4;
        }

        .funnel {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            margin: 24px 0;
            flex-wrap: wrap;
        }
        .funnel-step {
            background: rgba(59,130,246,0.2);
            border: 1px solid #3b82f6;
            padding: 12px 20px;
            border-radius: 8px;
            text-align: center;
        }
        .funnel-step.problem {
            background: rgba(239,68,68,0.2);
            border-color: #ef4444;
        }
        .funnel-step .num { font-size: 1.5rem; font-weight: 700; }
        .funnel-step .label { font-size: 0.75rem; color: #94a3b8; }
        .funnel-arrow { color: #64748b; font-size: 1.5rem; }

        .summary-box {
            background: linear-gradient(135deg, #1e3a5f, #1e293b);
            border: 2px solid #3b82f6;
            border-radius: 16px;
            padding: 24px;
            text-align: center;
        }
        .summary-box h3 { color: #60a5fa; margin-bottom: 16px; }
        .summary-box p { font-size: 1.1rem; line-height: 1.6; }

        .footer {
            text-align: center;
            color: #64748b;
            font-size: 0.85rem;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }

        @media (max-width: 768px) {
            .metrics-grid { grid-template-columns: 1fr; }
            .funnel { flex-direction: column; }
            .funnel-arrow { transform: rotate(90deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Meta Ads Performance Analysis</h1>
            <p class="subtitle">PrepAiro UPSC - Final Diagnostic Report</p>
            <p class="date">Generated: ''' + datetime.now().strftime('%B %d, %Y at %I:%M %p IST') + '''</p>
        </div>

        <div class="alert">
            <h3>⚠️ Critical Performance Drop Detected</h3>
            <p>Daily installs dropped from <strong>42/day</strong> to <strong>3.5/day</strong> (92% decline). Cost per install increased from <strong>₹94</strong> to <strong>₹765</strong> (8x increase).</p>
        </div>

        <!-- Performance Summary -->
        <div class="section">
            <h2>📉 Performance Summary</h2>
            <div class="metrics-grid">
                <div class="metric-card bad">
                    <div class="label">Installs (Jan 31-Feb 5)</div>
                    <div class="value">21</div>
                    <div class="change" style="color:#ef4444">↓ 92% vs peak</div>
                </div>
                <div class="metric-card bad">
                    <div class="label">Cost Per Install</div>
                    <div class="value">₹765</div>
                    <div class="change" style="color:#ef4444">↑ 714% vs peak</div>
                </div>
                <div class="metric-card bad">
                    <div class="label">Daily Spend Efficiency</div>
                    <div class="value">3.5</div>
                    <div class="change" style="color:#ef4444">installs/day (was 42)</div>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>Installs</th>
                        <th>Daily Avg</th>
                        <th>CPI</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Jan 23-25 (Peak)</td>
                        <td><strong>126</strong></td>
                        <td>42/day</td>
                        <td>₹94</td>
                        <td style="color:#10b981">✅ Excellent</td>
                    </tr>
                    <tr>
                        <td>Jan 26-30 (Decline)</td>
                        <td>72</td>
                        <td>14/day</td>
                        <td>₹174</td>
                        <td style="color:#f59e0b">⚠️ Declining</td>
                    </tr>
                    <tr>
                        <td>Jan 31-Feb 5 (Crash)</td>
                        <td><strong>21</strong></td>
                        <td>3.5/day</td>
                        <td>₹765</td>
                        <td style="color:#ef4444">🔴 Critical</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Root Causes -->
        <div class="section">
            <h2>🔍 Root Causes Identified</h2>

            <div class="cause-item">
                <h4>1. Best Performing Campaign Was Stopped</h4>
                <p><code>PrepAiro_Install_Value_Dec25</code> had the best CPI (₹32.5) and was turned off after January 25th, removing your most efficient install source.</p>
                <div class="evidence">
                    Peak Performance: ₹1,073 spend → 33 installs → CPI ₹32.5<br>
                    After Jan 25: ₹0 spend → Campaign STOPPED
                </div>
            </div>

            <div class="cause-item">
                <h4>2. Wrong Campaign Objective</h4>
                <p><code>UPSC_Checkouts</code> campaign uses <strong>OUTCOME_SALES</strong> objective, which optimizes for checkouts instead of app installs. Meta's algorithm started finding checkout-likely users instead of install-likely users.</p>
                <div class="evidence">
                    Objective: OUTCOME_SALES (should be APP_INSTALLS)<br>
                    Optimization: OFFSITE_CONVERSIONS<br>
                    Result: Checkouts ↑ (12→23) but Installs ↓ (93→14)
                </div>
            </div>

            <div class="cause-item">
                <h4>3. Winning Ads Were Paused</h4>
                <p>Your top-performing video ads were paused, removing the creatives that drove 115 installs.</p>
                <div class="evidence">
                    VID_BiryaniSasti_Skit: 85 installs (₹86 CPI) → PAUSED<br>
                    VID_KaranAujla_PriceDrop: 21 installs (₹172 CPI) → PAUSED<br>
                    VID_PriceDropDance_Group: 9 installs (₹157 CPI) → PAUSED
                </div>
            </div>

            <div class="cause-item">
                <h4>4. Budget Diverted to Non-Install Campaign</h4>
                <p><code>UPSC_Web_Conversions</code> received ₹5,736 but generated zero app installs because it optimizes for web events.</p>
                <div class="evidence">
                    UPSC_Web_Conversions_Jan26: ₹5,736 spend → 0 installs<br>
                    Wasted budget that could have driven ~65 installs
                </div>
            </div>

            <div class="cause-item">
                <h4>5. Static Ads Replaced Winning Videos</h4>
                <p>New static image ads launched on Feb 4 to replace the paused videos, but they have zero installs.</p>
                <div class="evidence">
                    PRO_CONV_UPSC_Mains_Checklist_Static: 0 installs<br>
                    PRO_CONV_UPSC_Price_Value_Static: 0 installs<br>
                    PRO_CONV_UPSC_Comparison_Static: 0 installs
                </div>
            </div>
        </div>

        <!-- What Happened -->
        <div class="section">
            <h2>📅 Timeline of Events</h2>
            <div class="timeline">
                <div class="timeline-item good">
                    <div class="timeline-date">January 23-25</div>
                    <div class="timeline-title">🟢 Peak Performance</div>
                    <div class="timeline-desc">126 installs over 3 days. Both install campaign and checkouts campaign driving installs efficiently.</div>
                </div>
                <div class="timeline-item warning">
                    <div class="timeline-date">~January 26</div>
                    <div class="timeline-title">🛑 Install Campaign Stopped</div>
                    <div class="timeline-desc">PrepAiro_Install_Value_Dec25 was turned off. Lost dedicated install optimization.</div>
                </div>
                <div class="timeline-item warning">
                    <div class="timeline-date">January 26-30</div>
                    <div class="timeline-title">⚠️ Algorithm Shift Begins</div>
                    <div class="timeline-desc">Checkouts campaign "learned" to find checkout users instead of installers. Install volume declining.</div>
                </div>
                <div class="timeline-item bad">
                    <div class="timeline-date">~January 28</div>
                    <div class="timeline-title">🎬 Winning Ads Paused</div>
                    <div class="timeline-desc">BiryaniSasti, KaranAujla, and PriceDropDance video ads were paused.</div>
                </div>
                <div class="timeline-item bad">
                    <div class="timeline-date">January 31+</div>
                    <div class="timeline-title">🔴 Performance Crash</div>
                    <div class="timeline-desc">Installs dropped to 3.5/day. Algorithm fully optimized for checkouts, ignoring potential installers.</div>
                </div>
                <div class="timeline-item bad">
                    <div class="timeline-date">February 2</div>
                    <div class="timeline-title">💀 Zero Installs Day</div>
                    <div class="timeline-desc">₹2,064 spent with 0 installs recorded. Complete funnel breakdown.</div>
                </div>
            </div>
        </div>

        <!-- The Funnel Problem -->
        <div class="section">
            <h2>🔄 The Funnel Problem</h2>
            <p style="margin-bottom:20px;color:#94a3b8;">Your conversion funnel requires installs first, but the campaign optimizes for checkouts instead.</p>

            <div class="funnel">
                <div class="funnel-step problem">
                    <div class="num">↓</div>
                    <div class="label">AD SHOWN</div>
                </div>
                <span class="funnel-arrow">→</span>
                <div class="funnel-step problem">
                    <div class="num">14</div>
                    <div class="label">INSTALLS (was 93)</div>
                </div>
                <span class="funnel-arrow">→</span>
                <div class="funnel-step">
                    <div class="num">11</div>
                    <div class="label">REGISTRATIONS</div>
                </div>
                <span class="funnel-arrow">→</span>
                <div class="funnel-step">
                    <div class="num">23</div>
                    <div class="label">CHECKOUTS</div>
                </div>
                <span class="funnel-arrow">→</span>
                <div class="funnel-step">
                    <div class="num">2</div>
                    <div class="label">PURCHASES</div>
                </div>
            </div>

            <div style="background:rgba(0,0,0,0.3);padding:20px;border-radius:12px;margin-top:20px;">
                <p><strong style="color:#ef4444;">The Problem:</strong> Meta is finding users who might checkout but don't install the app first. Without installs at the top, the funnel starves.</p>
                <p style="margin-top:12px;"><strong style="color:#10b981;">The Solution:</strong> Use APP_INSTALLS objective to fill the top of funnel, then retarget installers for checkouts.</p>
            </div>
        </div>

        <!-- Recommendations -->
        <div class="section">
            <h2>✅ Recommended Actions</h2>

            <div class="recommendation">
                <div class="rec-priority">1</div>
                <div class="rec-content">
                    <h4>Unpause Winning Video Ads</h4>
                    <p>Immediately unpause VID_BiryaniSasti_Skit (85 installs, ₹86 CPI) and VID_KaranAujla_PriceDrop (21 installs).</p>
                    <div class="rec-impact">Expected impact: +15-20 installs/day</div>
                </div>
            </div>

            <div class="recommendation">
                <div class="rec-priority">2</div>
                <div class="rec-content">
                    <h4>Restart Install Campaign</h4>
                    <p>Turn PrepAiro_Install_Value_Dec25 back on. It had CPI of ₹32.5 - your most efficient campaign.</p>
                    <div class="rec-impact">Expected impact: +10-15 installs/day</div>
                </div>
            </div>

            <div class="recommendation">
                <div class="rec-priority">3</div>
                <div class="rec-content">
                    <h4>Pause Web Conversions Campaign</h4>
                    <p>UPSC_Web_Conversions spent ₹5,736 with 0 installs. Pause it or change objective to APP_INSTALLS.</p>
                    <div class="rec-impact">Expected impact: Save ₹1,000/day in wasted spend</div>
                </div>
            </div>

            <div class="recommendation">
                <div class="rec-priority">4</div>
                <div class="rec-content">
                    <h4>Create Dedicated Install Campaign</h4>
                    <p>Launch new campaign with APP_INSTALLS objective. This fills the top of your funnel with new users.</p>
                    <div class="rec-impact">Expected impact: Restore funnel health, sustainable growth</div>
                </div>
            </div>

            <div class="recommendation">
                <div class="rec-priority">5</div>
                <div class="rec-content">
                    <h4>Restructure Campaign Strategy</h4>
                    <p>Use two-campaign approach: (1) Install campaign for new users, (2) Retargeting campaign for conversions.</p>
                    <div class="rec-impact">Expected impact: Proper funnel optimization, lower overall CPA</div>
                </div>
            </div>
        </div>

        <!-- Summary -->
        <div class="summary-box">
            <h3>📋 One-Line Diagnosis</h3>
            <p>Your best campaign was stopped, winning ads were paused, and remaining campaigns optimize for checkouts instead of installs - starving your funnel of new users.</p>
        </div>

        <div class="footer">
            <p>PrepAiro UPSC - Meta Ads Performance Analysis</p>
            <p style="margin-top:8px;">Analysis Period: January 20 - February 5, 2026</p>
        </div>
    </div>
</body>
</html>
'''

# Save locally
os.makedirs('charts', exist_ok=True)
with open('charts/final_report.html', 'w') as f:
    f.write(html)
print("Report saved locally")

# Upload to S3
s3 = boto3.client('s3', region_name='ap-south-1')
key = f'meta-ads-charts/{datetime.now().strftime("%Y%m%d_%H%M%S")}_final_report.html'
s3.upload_file('charts/final_report.html', 'prepairo-analytics-reports', key, ExtraArgs={'ContentType': 'text/html'})
url = f"https://prepairo-analytics-reports.s3.ap-south-1.amazonaws.com/{key}"
print(f"\n✅ Report uploaded: {url}")
