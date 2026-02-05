"""
Slack formatter - sends multiple messages for large reports
"""

import requests
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

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
            
            # MESSAGE 1: Header + Summary + AI Insights
            message1_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 {account_name} - Daily Report",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📅 Data:* {date_display} (Full Day - IST)\n*🕐 Report Generated:* {time_str}\n*💰 Balance:* {balance.get('balance_formatted', '₹0.00')}"
                    }
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*📈 Account Summary (vs. Previous Day)*\n"
                            f"• Spend: ₹{spend_delta.get('current', 0):,.2f} ({self._format_delta(spend_delta.get('percent', 0))})\n"
                            f"• Impressions: {int(imp_delta.get('current', 0)):,} ({self._format_delta(imp_delta.get('percent', 0))})\n"
                            f"• Clicks: {int(clicks_delta.get('current', 0)):,} ({self._format_delta(clicks_delta.get('percent', 0))})"
                        )
                    }
                },
                {"type": "divider"}
            ]
            
            # Add AI insights (truncate if too long)
            if current_analysis and not current_analysis.startswith("⚠️"):
                # Truncate to 2500 chars if needed
                truncated_current = current_analysis[:2500] + "..." if len(current_analysis) > 2500 else current_analysis
                message1_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🤖 AI Analysis: This Window*\n{truncated_current}"
                    }
                })
                message1_blocks.append({"type": "divider"})
            
            if trend_analysis and not trend_analysis.startswith("⏳"):
                truncated_trend = trend_analysis[:2500] + "..." if len(trend_analysis) > 2500 else trend_analysis
                message1_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📊 AI Analysis: Trends*\n{truncated_trend}"
                    }
                })
            elif trend_analysis.startswith("⏳"):
                message1_blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": trend_analysis}
                })
            
            # Add PNG chart image if available
            if charts.get('png_url'):
                message1_blocks.append({"type": "divider"})
                message1_blocks.append({
                    "type": "image",
                    "image_url": charts['png_url'],
                    "alt_text": "Campaign Performance Chart"
                })
            
            # MESSAGE 2: Campaign Details
            message2_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 Campaign Breakdown ({len(campaigns)} Campaigns)",
                        "emoji": True
                    }
                },
                {"type": "divider"}
            ]
            
            campaigns_sorted = sorted(campaigns, key=lambda x: float(x.get('spend', 0)), reverse=True)
            
            for camp_idx, campaign in enumerate(campaigns_sorted, 1):
                camp_id = campaign.get('campaign_id')
                camp_name = campaign.get('campaign_name', 'Unknown')
                camp_spend = float(campaign.get('spend', 0))
                camp_imp = int(campaign.get('impressions', 0))
                camp_reach = int(campaign.get('reach', 0))
                camp_clicks = int(campaign.get('clicks', 0))
                camp_ctr = (camp_clicks / camp_imp * 100) if camp_imp > 0 else 0
                camp_status = campaign.get('effective_status', 'UNKNOWN')

                campaign_delta = deltas.get('campaigns', [])
                delta_pct = 0
                for cd in campaign_delta:
                    if cd.get('campaign_id') == camp_id:
                        delta_pct = cd.get('delta_spend', {}).get('percent', 0)
                        break

                trend_emoji = self._get_trend_emoji(delta_pct)
                status_emoji = self._get_status_emoji(camp_status)

                campaign_text = (
                    f"*{camp_idx}. {camp_name[:45]}* {status_emoji} {trend_emoji}\n"
                    f"💰 ₹{camp_spend:,.2f} | 👁️ {camp_imp:,} | 👥 {camp_reach:,} | 🖱️ {camp_clicks} | 📊 {camp_ctr:.2f}%\n"
                )
                
                # AdSets for this campaign
                camp_adsets = [a for a in adsets if a.get('campaign_id') == camp_id]
                camp_adsets_sorted = sorted(camp_adsets, key=lambda x: float(x.get('spend', 0)), reverse=True)
                
                if camp_adsets_sorted:
                    campaign_text += f"\n*AdSets ({len(camp_adsets_sorted)}):*\n"
                    for adset in camp_adsets_sorted:
                        adset_name = adset.get('adset_name', 'Unknown')[:35]
                        adset_spend = float(adset.get('spend', 0))
                        adset_imp = int(adset.get('impressions', 0))
                        adset_clicks = int(adset.get('clicks', 0))
                        adset_ctr = (adset_clicks / adset_imp * 100) if adset_imp > 0 else 0
                        adset_status = adset.get('effective_status', 'UNKNOWN')
                        adset_status_emoji = self._get_status_emoji(adset_status)

                        campaign_text += f"  • {adset_status_emoji} {adset_name}: ₹{adset_spend:,.2f} | {adset_imp:,} imp | {adset_clicks} clicks | {adset_ctr:.2f}%\n"
                
                message2_blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": campaign_text}
                })
            
            # MESSAGE 3: Ad Details
            message3_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🎨 Ad Performance ({len(ads)} Ads)",
                        "emoji": True
                    }
                },
                {"type": "divider"}
            ]
            
            ads_sorted = sorted(ads, key=lambda x: float(x.get('spend', 0)), reverse=True)
            
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

                status_emoji = self._get_status_emoji(ad_status)

                ad_text = (
                    f"\n*{ad_idx}. {ad_name}* {status_emoji}\n"
                    f"   📁 Campaign: {campaign_name}\n"
                    f"   📂 AdSet: {adset_name}\n"
                    f"   💰 Spend: ₹{ad_spend:,.2f} | "
                    f"{ad_imp:,} imp | "
                    f"{ad_clicks:,} clicks ({ad_ctr:.2f}%)"
                )
                
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
