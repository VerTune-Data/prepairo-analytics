"""
Slack formatter - sends multiple messages for large reports
"""

import requests
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from modules.table_formatter import TableFormatter

logger = logging.getLogger(__name__)


class SlackFormatter:
    """Format and send Slack messages (splits into multiple if needed)"""
    
    MAX_BLOCKS_PER_MESSAGE = 45  # Slack limit is 50, keep buffer
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def format_6hour_report(self, snapshot_data: Dict, deltas: Dict, claude_insights: Tuple[str, str], 
                           charts: Dict, account_name: str, interval_hours: int = 8) -> List[List[Dict]]:
        """
        Format report and split into multiple messages if needed
        Returns list of message blocks
        """
        try:
            current_analysis, trend_analysis = claude_insights
            
            # Extract data
            snapshot_time = snapshot_data.get('snapshot_time', datetime.now())
            date_since = snapshot_data.get('date_since', '')
            window_number = snapshot_data.get('window_number', 0)
            balance = snapshot_data.get('balance', {})
            campaigns = snapshot_data.get('campaigns', [])
            adsets = snapshot_data.get('adsets', [])
            ads = snapshot_data.get('ads', [])
            
            # Format time and date
            if isinstance(snapshot_time, str):
                snapshot_time = datetime.fromisoformat(snapshot_time)
            time_str = snapshot_time.strftime('%b %d, %Y %I:%M %p IST')

            # Format yesterday's date nicely
            if date_since:
                from datetime import datetime as dt
                yesterday_dt = dt.strptime(date_since, '%Y-%m-%d')
                date_display = yesterday_dt.strftime('%b %d, %Y')
            else:
                date_display = "Yesterday"
            
            account_deltas = deltas.get('account', {})
            spend_delta = account_deltas.get('spend', {})
            imp_delta = account_deltas.get('impressions', {})
            clicks_delta = account_deltas.get('clicks', {})

            # Calculate total conversions
            total_installs = 0
            total_registrations = 0
            total_checkouts = 0
            total_purchases = 0
            for camp in campaigns:
                parsed = camp.get('parsed_actions', {})
                total_installs += int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or parsed.get('mobile_app_install', 0))
                total_registrations += int(parsed.get('omni_complete_registration', 0) or parsed.get('complete_registration', 0))
                total_checkouts += int(parsed.get('omni_initiated_checkout', 0) or parsed.get('initiated_checkout', 0))
                total_purchases += int(parsed.get('omni_purchase', 0) or parsed.get('purchase', 0))

            # Calculate average costs
            total_spend = spend_delta.get('current', 0)
            avg_cpi = (total_spend / total_installs) if total_installs > 0 else 0
            avg_cpr = (total_spend / total_registrations) if total_registrations > 0 else 0
            avg_cpa = (total_spend / total_purchases) if total_purchases > 0 else 0
            
            # MESSAGE 1: Header + Summary + AI Insights
            message1_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{account_name} - Daily Performance Report",
                        "emoji": False
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Date:* {date_display} | *Generated:* {time_str}\n*Budget Remaining:* {balance.get('balance_formatted', '₹0.00')}"
                    }
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*Account Summary*\n"
                            f"Spend: ₹{spend_delta.get('current', 0):,.2f} ({self._format_delta(spend_delta.get('percent', 0))})\n"
                            f"Impressions: {int(imp_delta.get('current', 0)):,} ({self._format_delta(imp_delta.get('percent', 0))})\n"
                            f"Clicks: {int(clicks_delta.get('current', 0)):,} ({self._format_delta(clicks_delta.get('percent', 0))})\n\n"
                            f"*Conversions*\n"
                            f"Installs: {total_installs} | CPI: ₹{avg_cpi:.0f}\n"
                            f"Registrations: {total_registrations} | CPR: ₹{avg_cpr:.0f}\n"
                            f"Purchases: {total_purchases} | CPA: ₹{avg_cpa:.0f}"
                        )
                    }
                },
                {"type": "divider"}
            ]
            
            # Add AI insights (truncate if too long)
            if current_analysis and not current_analysis.startswith("⚠️"):
                truncated_current = current_analysis[:2500] + "..." if len(current_analysis) > 2500 else current_analysis
                message1_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*AI Analysis*\n{truncated_current}"
                    }
                })
                message1_blocks.append({"type": "divider"})

            if trend_analysis and not trend_analysis.startswith("⏳"):
                truncated_trend = trend_analysis[:2500] + "..." if len(trend_analysis) > 2500 else trend_analysis
                message1_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Trend Analysis*\n{truncated_trend}"
                    }
                })
            elif trend_analysis.startswith("⏳"):
                message1_blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": trend_analysis}
                })

            # Add PNG chart images if available
            if charts.get('traffic_url'):
                message1_blocks.append({"type": "divider"})
                message1_blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Traffic Metrics*"}
                })
                message1_blocks.append({
                    "type": "image",
                    "image_url": charts['traffic_url'],
                    "alt_text": "Traffic Metrics Chart"
                })

            if charts.get('conversion_url'):
                message1_blocks.append({"type": "divider"})
                message1_blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Conversion Metrics*"}
                })
                message1_blocks.append({
                    "type": "image",
                    "image_url": charts['conversion_url'],
                    "alt_text": "Conversion Metrics Chart"
                })

            # Add dashboard link if available
            if charts.get('dashboard_url'):
                message1_blocks.append({"type": "divider"})
                message1_blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Dashboard:* <{charts['dashboard_url']}|View Interactive Dashboard>"}
                })

            # MESSAGE 2: Campaign Details
            # Filter campaigns with spend > 0
            campaigns_with_spend = [c for c in campaigns if float(c.get('spend', 0)) > 0]
            campaigns_sorted = sorted(campaigns_with_spend, key=lambda x: float(x.get('spend', 0)), reverse=True)

            message2_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Campaign Breakdown ({len(campaigns_sorted)} Active)",
                        "emoji": False
                    }
                },
                {"type": "divider"}
            ]

            actual_idx = 0
            for campaign in campaigns_sorted:
                actual_idx += 1
                camp_id = campaign.get('campaign_id')
                camp_name = campaign.get('campaign_name', 'Unknown')
                camp_spend = float(campaign.get('spend', 0))

                # Skip campaigns with 0 spend
                if camp_spend == 0:
                    continue

                camp_imp = int(campaign.get('impressions', 0))
                camp_reach = int(campaign.get('reach', 0))
                camp_clicks = int(campaign.get('clicks', 0))
                camp_ctr = (camp_clicks / camp_imp * 100) if camp_imp > 0 else 0
                camp_status = campaign.get('effective_status', 'UNKNOWN')

                # Extract conversions
                parsed = campaign.get('parsed_actions', {})
                installs = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or parsed.get('mobile_app_install', 0))
                registrations = int(parsed.get('omni_complete_registration', 0) or parsed.get('complete_registration', 0))
                checkouts = int(parsed.get('omni_initiated_checkout', 0) or parsed.get('initiated_checkout', 0))
                purchases = int(parsed.get('omni_purchase', 0) or parsed.get('purchase', 0))

                # Calculate costs
                cpi = (camp_spend / installs) if installs > 0 else 0
                cpr = (camp_spend / registrations) if registrations > 0 else 0
                cpa = (camp_spend / purchases) if purchases > 0 else 0

                campaign_delta = deltas.get('campaigns', [])
                delta_pct = 0
                for cd in campaign_delta:
                    if cd.get('campaign_id') == camp_id:
                        delta_pct = cd.get('delta_spend', {}).get('percent', 0)
                        break

                trend_indicator = self._get_trend_text(delta_pct)
                status_text = f"[{camp_status}]"

                campaign_text = (
                    f"*{actual_idx}. {camp_name[:45]}* {status_text}\n"
                    f"Spend: ₹{camp_spend:,.2f} | Impr: {camp_imp:,} | Clicks: {camp_clicks} | CTR: {camp_ctr:.2f}%\n"
                )

                # Add conversion metrics if available
                conv_parts = []
                if installs > 0:
                    conv_parts.append(f"{installs} installs (CPI ₹{cpi:.0f})")
                if registrations > 0:
                    conv_parts.append(f"{registrations} regs (CPR ₹{cpr:.0f})")
                if purchases > 0:
                    conv_parts.append(f"{purchases} purchases (CPA ₹{cpa:.0f})")

                if conv_parts:
                    campaign_text += f"Conversions: {' | '.join(conv_parts)}\n"
                
                # AdSets for this campaign
                camp_adsets = [a for a in adsets if a.get('campaign_id') == camp_id]
                camp_adsets_sorted = sorted(camp_adsets, key=lambda x: float(x.get('spend', 0)), reverse=True)
                
                if camp_adsets_sorted:
                    # Filter out 0 spend adsets
                    active_adsets = [a for a in camp_adsets_sorted if float(a.get('spend', 0)) > 0]
                    if active_adsets:
                        campaign_text += f"\n*AdSets ({len(active_adsets)}):*\n"
                        for adset in active_adsets:
                            adset_name = adset.get('adset_name', 'Unknown')[:35]
                            adset_spend = float(adset.get('spend', 0))
                            adset_imp = int(adset.get('impressions', 0))
                            adset_clicks = int(adset.get('clicks', 0))
                            adset_ctr = (adset_clicks / adset_imp * 100) if adset_imp > 0 else 0
                            adset_status = adset.get('effective_status', 'UNKNOWN')

                            # Extract conversions
                            parsed = adset.get('parsed_actions', {})
                            installs = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or parsed.get('mobile_app_install', 0))
                            registrations = int(parsed.get('omni_complete_registration', 0) or parsed.get('complete_registration', 0))
                            purchases = int(parsed.get('omni_purchase', 0) or parsed.get('purchase', 0))

                            conv_summary = []
                            if installs > 0:
                                adset_cpi = adset_spend / installs
                                conv_summary.append(f"{installs} inst (₹{adset_cpi:.0f})")
                            if registrations > 0:
                                adset_cpr = adset_spend / registrations
                                conv_summary.append(f"{registrations} reg (₹{adset_cpr:.0f})")
                            if purchases > 0:
                                adset_cpa = adset_spend / purchases
                                conv_summary.append(f"{purchases} pur (₹{adset_cpa:.0f})")

                            conv_str = f" | {', '.join(conv_summary)}" if conv_summary else ""

                            campaign_text += f"  - {adset_name}: ₹{adset_spend:,.2f} | {adset_imp:,} imp | {adset_clicks} clicks | {adset_ctr:.2f}%{conv_str}\n"
                
                message2_blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": campaign_text}
                })
            
            # MESSAGE 3: Ad Details
            # Filter out ads with 0 spend
            ads_with_spend = [ad for ad in ads if float(ad.get('spend', 0)) > 0]
            ads_sorted = sorted(ads_with_spend, key=lambda x: float(x.get('spend', 0)), reverse=True)

            message3_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Ad Performance ({len(ads_sorted)} Active)",
                        "emoji": False
                    }
                },
                {"type": "divider"}
            ]

            if not ads_sorted:
                message3_blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "_No ads with spend in this period_"}
                })

            for ad_idx, ad in enumerate(ads_sorted, 1):
                # Extract full hierarchy
                campaign_name = ad.get('campaign_name', 'Unknown Campaign')[:30]
                adset_name = ad.get('adset_name', 'Unknown AdSet')[:30]
                ad_name = ad.get('ad_name', 'Unknown Ad')[:35]
                ad_status = ad.get('effective_status', 'UNKNOWN')

                ad_spend = float(ad.get('spend', 0))
                ad_imp = int(ad.get('impressions', 0))
                ad_clicks = int(ad.get('clicks', 0))
                ad_ctr = (ad_clicks / ad_imp * 100) if ad_imp > 0 else 0

                # Extract conversions
                parsed = ad.get('parsed_actions', {})
                installs = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or parsed.get('mobile_app_install', 0))
                registrations = int(parsed.get('omni_complete_registration', 0) or parsed.get('complete_registration', 0))
                checkouts = int(parsed.get('omni_initiated_checkout', 0) or parsed.get('initiated_checkout', 0))
                purchases = int(parsed.get('omni_purchase', 0) or parsed.get('purchase', 0))

                status_emoji = self._get_status_emoji(ad_status)

                ad_text = (
                    f"\n*{ad_idx}. {ad_name}* {status_emoji}\n"
                    f"   📁 Campaign: {campaign_name}\n"
                    f"   📂 AdSet: {adset_name}\n"
                    f"   💰 Spend: ₹{ad_spend:,.2f} | "
                    f"{ad_imp:,} imp | "
                    f"{ad_clicks:,} clicks ({ad_ctr:.2f}%)"
                )

                # Add conversions if available
                conv_parts = []
                if installs > 0:
                    cpi = ad_spend / installs
                    conv_parts.append(f"{installs} inst (₹{cpi:.0f} CPI)")
                if registrations > 0:
                    cpr = ad_spend / registrations
                    conv_parts.append(f"{registrations} reg (₹{cpr:.0f} CPR)")
                if checkouts > 0:
                    conv_parts.append(f"{checkouts} checkout")
                if purchases > 0:
                    cpa = ad_spend / purchases
                    conv_parts.append(f"{purchases} pur (₹{cpa:.0f} CPA)")

                if conv_parts:
                    ad_text += f"\n   🎯 Conversions: {' | '.join(conv_parts)}"

                message3_blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": ad_text}
                })
            
            # Add end separator to last message
            message3_blocks.append({"type": "divider"})
            message3_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                }
            })
            
            return [message1_blocks, message2_blocks, message3_blocks]
        
        except Exception as e:
            logger.error(f"Error formatting report: {e}", exc_info=True)
            return [[{
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"❌ Error: {e}"}
            }]]
    
    def _format_delta(self, percent: float) -> str:
        if percent > 5:
            return f"↑ +{percent:.1f}%"
        elif percent < -5:
            return f"↓ {percent:.1f}%"
        else:
            return f"→ {percent:+.1f}%"
    
    def _get_trend_emoji(self, delta_pct: float) -> str:
        if abs(delta_pct) < 5:
            return ""
        elif delta_pct > 20:
            return "🚀"
        elif delta_pct > 5:
            return "📈"
        elif delta_pct < -20:
            return "📉"
        elif delta_pct < -5:
            return "⚠️"
        return ""

    def _get_trend_text(self, delta_pct: float) -> str:
        """Get trend indicator as text instead of emoji"""
        if abs(delta_pct) < 5:
            return ""
        elif delta_pct > 0:
            return f"(+{delta_pct:.0f}%)"
        else:
            return f"({delta_pct:.0f}%)"

    def _get_status_emoji(self, status: str) -> str:
        """Get status emoji for campaign/adset/ad status"""
        status_map = {
            'ACTIVE': '✅',
            'PAUSED': '⏸️',
            'DELETED': '🗑️',
            'ARCHIVED': '📦',
            'PENDING_REVIEW': '⏳',
            'DISAPPROVED': '❌',
            'PREAPPROVED': '🟡',
            'PENDING_BILLING_INFO': '💳',
            'CAMPAIGN_PAUSED': '⏸️',
            'ADSET_PAUSED': '⏸️',
            'IN_PROCESS': '🔄',
            'WITH_ISSUES': '⚠️'
        }
        return status_map.get(status, '❓')
    
    def _format_conversion_metrics(self, parsed_actions: dict) -> str:
        """Format conversion metrics for display"""
        if not parsed_actions:
            return ""
        
        lines = []
        
        # Check for installs
        installs = parsed_actions.get("omni_app_install", 0) or parsed_actions.get("app_install", 0) or parsed_actions.get("mobile_app_install", 0)
        cpi = parsed_actions.get("omni_app_install_cost", 0) or parsed_actions.get("app_install_cost", 0) or parsed_actions.get("mobile_app_install_cost", 0)
        if installs > 0:
            lines.append(f"📲 {int(installs):,} installs (CPI: ₹{cpi:.2f})")
        
        # Check for registrations
        registrations = parsed_actions.get("omni_complete_registration", 0) or parsed_actions.get("complete_registration", 0)
        cpr = parsed_actions.get("omni_complete_registration_cost", 0) or parsed_actions.get("complete_registration_cost", 0)
        if registrations > 0:
            lines.append(f"✍️ {int(registrations):,} registrations (CPR: ₹{cpr:.2f})")
        
        # Check for purchases
        purchases = parsed_actions.get("omni_purchase", 0) or parsed_actions.get("purchase", 0)
        cpa = parsed_actions.get("omni_purchase_cost", 0) or parsed_actions.get("purchase_cost", 0)
        if purchases > 0:
            lines.append(f"💰 {int(purchases):,} purchases (CPA: ₹{cpa:.2f})")
        
        return " | ".join(lines) if lines else "No conversions"
    
    def send_to_slack(self, messages: List[List[Dict]], attachments: Optional[List[str]] = None) -> bool:
        """Send multiple messages to Slack"""
        try:
            success = True
            for idx, blocks in enumerate(messages, 1):
                payload = {"blocks": blocks}
                
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent message {idx}/{len(messages)} to Slack")
                else:
                    logger.error(f"Slack webhook failed for message {idx}: {response.status_code} - {response.text}")
                    success = False
            
            return success
        
        except Exception as e:
            logger.error(f"Error sending to Slack: {e}")
            return False
    
    def send_first_run_message(self, snapshot_data: Dict, current_analysis: str, charts: Dict, account_name: str):
        """Send first run report"""
        try:
            deltas = {
                'account': {
                    'spend': {'current': sum(float(c.get('spend', 0)) for c in snapshot_data.get('campaigns', [])), 'percent': 0},
                    'impressions': {'current': sum(int(c.get('impressions', 0)) for c in snapshot_data.get('campaigns', [])), 'percent': 0},
                    'clicks': {'current': sum(int(c.get('clicks', 0)) for c in snapshot_data.get('campaigns', [])), 'percent': 0}
                },
                'campaigns': [],
                'significant_changes': []
            }
            
            claude_insights = (current_analysis, "⏳ No previous data - trend analysis will be available in next daily report")
            
            messages = self.format_6hour_report(snapshot_data, deltas, claude_insights, charts, account_name)
            self.send_to_slack(messages)
        
        except Exception as e:
            logger.error(f"Error sending first run message: {e}", exc_info=True)
    
    def send_error_message(self, error_msg: str, account_name: str):
        """Send error notification"""
        blocks = [[{
            "type": "header",
            "text": {"type": "plain_text", "text": f"❌ {account_name} - Error", "emoji": True}
        }, {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"```{error_msg}```"}
        }]]
        
        self.send_to_slack(blocks)
