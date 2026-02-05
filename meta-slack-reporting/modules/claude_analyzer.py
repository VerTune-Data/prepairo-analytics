"""
Claude AI analyzer with Slack-compatible formatting
"""

import logging
from typing import Dict, Optional, Tuple, List
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeAnalyzer:
    """Claude AI integration for Meta Ads analysis"""
    
    def __init__(self, api_key: str, model: str = 'claude-sonnet-4-5-20250929'):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.last_prompt = None
    
    def analyze_6hour_window(self, current_data: Dict, previous_data: Optional[Dict], account_name: str) -> Tuple[str, str]:
        """
        Analyze yesterday's complete data with Slack formatting
        Returns tuple: (current_analysis, trend_analysis)
        """
        try:
            current_prompt = self._build_current_analysis_prompt(current_data, account_name)
            current_analysis = self._call_claude(current_prompt)

            trend_analysis = ""
            if previous_data:
                trend_prompt = self._build_trend_analysis_prompt(current_data, previous_data, account_name)
                trend_analysis = self._call_claude(trend_prompt)
            else:
                trend_analysis = "⏳ No previous data - trend analysis will be available in next daily report"

            return current_analysis, trend_analysis
        
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            error_msg = f"⚠️ AI analysis unavailable: {str(e)}"
            return error_msg, error_msg
    
    def _call_claude(self, prompt: str) -> str:
        """Call Claude API with prompt"""
        logger.info(f"Calling Claude API ({self.model})")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis = response.content[0].text
        logger.info(f"Claude analysis received ({len(analysis)} chars)")
        
        return analysis
    
    def _extract_conversion_summary(self, campaigns: List) -> str:
        """Extract and summarize conversion data from campaigns"""
        total_installs = 0
        total_registrations = 0
        total_purchases = 0
        total_spend = 0
        
        for campaign in campaigns:
            parsed = campaign.get("parsed_actions", {})
            total_installs += parsed.get("omni_app_install", 0) or parsed.get("app_install", 0) or parsed.get("mobile_app_install", 0)
            total_registrations += parsed.get("omni_complete_registration", 0) or parsed.get("complete_registration", 0)
            total_purchases += parsed.get("omni_purchase", 0) or parsed.get("purchase", 0)
            total_spend += float(campaign.get("spend", 0))
        
        lines = []
        if total_installs > 0:
            cpi = total_spend / total_installs
            lines.append(f"- App Installs: {int(total_installs):,} (CPI: ₹{cpi:.2f})")
        if total_registrations > 0:
            cpr = total_spend / total_registrations
            lines.append(f"- Registrations: {int(total_registrations):,} (CPR: ₹{cpr:.2f})")
        if total_purchases > 0:
            cpa = total_spend / total_purchases
            lines.append(f"- Purchases: {int(total_purchases):,} (CPA: ₹{cpa:.2f})")
        
        return "\n".join(lines) if lines else "No conversion data available"
    
    def _build_current_analysis_prompt(self, current_data: Dict, account_name: str) -> str:
        """Build prompt for current window analysis with Slack formatting"""
        
        campaigns = current_data.get('campaigns', [])
        adsets = current_data.get('adsets', [])
        ads = current_data.get('ads', [])
        balance = current_data.get('balance', {})
        
        # Build detailed breakdown
        detailed_breakdown = []
        for camp in sorted(campaigns, key=lambda x: float(x.get('spend', 0)), reverse=True):
            camp_id = camp.get('campaign_id')
            camp_name = camp.get('campaign_name', 'Unknown')
            camp_spend = float(camp.get('spend', 0))

            # Skip campaigns with 0 spend
            if camp_spend == 0:
                continue

            camp_imp = int(camp.get('impressions', 0))
            camp_clicks = int(camp.get('clicks', 0))

            # Extract conversions
            parsed = camp.get('parsed_actions', {})
            installs = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or parsed.get('mobile_app_install', 0))
            registrations = int(parsed.get('omni_complete_registration', 0) or parsed.get('complete_registration', 0))
            checkouts = int(parsed.get('omni_initiated_checkout', 0) or parsed.get('initiated_checkout', 0))
            purchases = int(parsed.get('omni_purchase', 0) or parsed.get('purchase', 0))

            # Calculate costs
            cpi = (camp_spend / installs) if installs > 0 else 0
            cpr = (camp_spend / registrations) if registrations > 0 else 0
            cpa = (camp_spend / purchases) if purchases > 0 else 0

            camp_detail = f"Campaign: {camp_name}\n"
            camp_detail += f"  Spend: ₹{camp_spend:,.2f} | Impressions: {camp_imp:,} | Clicks: {camp_clicks}\n"

            # Add conversions if available
            conv_parts = []
            if installs > 0:
                conv_parts.append(f"{installs} installs (CPI: ₹{cpi:.2f})")
            if registrations > 0:
                conv_parts.append(f"{registrations} registrations (CPR: ₹{cpr:.2f})")
            if checkouts > 0:
                conv_parts.append(f"{checkouts} checkouts")
            if purchases > 0:
                conv_parts.append(f"{purchases} purchases (CPA: ₹{cpa:.2f})")

            if conv_parts:
                camp_detail += f"  Conversions: {' | '.join(conv_parts)}\n"
            
            camp_adsets = [a for a in adsets if a.get('campaign_id') == camp_id and float(a.get('spend', 0)) > 0]
            if camp_adsets:
                camp_detail += f"  AdSets ({len(camp_adsets)}):\n"
                for adset in sorted(camp_adsets, key=lambda x: float(x.get('spend', 0)), reverse=True):
                    adset_id = adset.get('adset_id')
                    adset_name = adset.get('adset_name', 'Unknown')[:35]
                    adset_spend = float(adset.get('spend', 0))

                    # Extract conversions
                    parsed = adset.get('parsed_actions', {})
                    installs = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or parsed.get('mobile_app_install', 0))
                    registrations = int(parsed.get('omni_complete_registration', 0) or parsed.get('complete_registration', 0))
                    purchases = int(parsed.get('omni_purchase', 0) or parsed.get('purchase', 0))

                    conv_str = ""
                    if installs > 0:
                        cpi = adset_spend / installs
                        conv_str += f" | {installs}i(₹{cpi:.0f})"
                    if registrations > 0:
                        cpr = adset_spend / registrations
                        conv_str += f" {registrations}r(₹{cpr:.0f})"
                    if purchases > 0:
                        cpa = adset_spend / purchases
                        conv_str += f" {purchases}p(₹{cpa:.0f})"

                    camp_detail += f"    - {adset_name}: ₹{adset_spend:,.2f}{conv_str}\n"

                    adset_ads = [a for a in ads if a.get('adset_id') == adset_id and float(a.get('spend', 0)) > 0]
                    for ad in sorted(adset_ads, key=lambda x: float(x.get('spend', 0)), reverse=True):
                        ad_name = ad.get('ad_name', 'Unknown')[:30]
                        ad_spend = float(ad.get('spend', 0))
                        ad_clicks = int(ad.get('clicks', 0))

                        # Extract ad conversions
                        parsed_ad = ad.get('parsed_actions', {})
                        ad_installs = int(parsed_ad.get('omni_app_install', 0) or parsed_ad.get('app_install', 0) or parsed_ad.get('mobile_app_install', 0))
                        ad_regs = int(parsed_ad.get('omni_complete_registration', 0) or parsed_ad.get('complete_registration', 0))
                        ad_purchases = int(parsed_ad.get('omni_purchase', 0) or parsed_ad.get('purchase', 0))

                        ad_conv_str = ""
                        if ad_installs > 0:
                            ad_conv_str += f" {ad_installs}i"
                        if ad_regs > 0:
                            ad_conv_str += f" {ad_regs}r"
                        if ad_purchases > 0:
                            ad_conv_str += f" {ad_purchases}p"

                        camp_detail += f"      • {ad_name}: ₹{ad_spend:,.2f} | {ad_clicks}c{ad_conv_str}\n"
            
            detailed_breakdown.append(camp_detail)
        
        prompt = f"""CRITICAL META ADS ANALYSIS for {account_name} - YESTERDAY'S DATA

You are analyzing a full day of Meta Ads performance. Find what's BLEEDING MONEY and what's PRINTING MONEY.

YESTERDAY'S FULL DATA:
{chr(10).join(detailed_breakdown)}

BUDGET STATUS: {balance.get('balance_formatted', '₹0.00 available')}
Prepaid Balance: ₹{balance.get('balance', 0):,.2f}

YOUR MISSION: Identify game-changing insights that could 10x results or prevent disaster.

SLACK FORMATTING (CRITICAL):
• Use *bold* for emphasis (NOT ** or ##)
• Use bullet points with •
• NO markdown headings (##, ###)
• Keep it punchy and actionable

Provide insights in this format:

*🚨 CRITICAL ALERTS*
• What's bleeding money NOW? (campaigns/adsets with high CPI/CPA/CPR but no conversions)
• Which campaigns to PAUSE immediately? (with exact ₹ wasted and poor conversion rates)
• Budget runway: How many days left at yesterday's spend rate?
• Any campaigns spending heavily with 0 installs/registrations/purchases?

*💎 CONVERSION WINNERS*
• Best CPI (Cost Per Install) - which campaign/adset/ad?
• Best CPR (Cost Per Registration) - exact numbers
• Best CPA (Cost Per Purchase) - which creative is converting?
• Highest conversion volume - installs, registrations, checkouts, purchases

*⚡ IMMEDIATE ACTIONS*
1. PAUSE: [Campaign X] - ₹[Y] spent, 0 conversions OR ₹[Z] CPI (target: ₹[A])
2. SCALE: [Campaign B] with ₹[C] CPI (best performer) - increase budget from ₹[D] to ₹[E]
3. OPTIMIZE: [Campaign C] - [F] installs but high CPI of ₹[G], test new creative

*📊 CONVERSION EFFICIENCY*
• Install funnel: impressions → clicks → installs (conversion rates)
• Registration funnel: where are users dropping off?
• Purchase funnel: checkouts vs completed purchases
• Which stage needs immediate attention?

*🎯 STRATEGIC MOVE*
• ONE game-changing recommendation focusing on conversion optimization
• Be specific with campaign names, exact CPI/CPA/CPR targets, and budget changes

Be ruthlessly honest. If something sucks, say it. If something's amazing, say why."""
        
        return prompt
    
    def _build_trend_analysis_prompt(self, current_data: Dict, previous_data: Dict, account_name: str) -> str:
        """Build trend analysis prompt with Slack formatting"""
        
        curr_campaigns = current_data.get('campaigns', [])
        curr_spend = sum(float(c.get('spend', 0)) for c in curr_campaigns)
        curr_impressions = sum(int(c.get('impressions', 0)) for c in curr_campaigns)
        curr_clicks = sum(int(c.get('clicks', 0)) for c in curr_campaigns)
        
        prev_campaigns = previous_data.get('campaigns', [])
        prev_spend = sum(float(c.get('spend', 0)) for c in prev_campaigns)
        prev_impressions = sum(int(c.get('impressions', 0)) for c in prev_campaigns)
        prev_clicks = sum(int(c.get('clicks', 0)) for c in prev_campaigns)
        
        delta_spend = curr_spend - prev_spend
        delta_spend_pct = (delta_spend / prev_spend * 100) if prev_spend > 0 else 0
        delta_impressions = curr_impressions - prev_impressions
        delta_impressions_pct = (delta_impressions / prev_impressions * 100) if prev_impressions > 0 else 0
        delta_clicks = curr_clicks - prev_clicks
        delta_clicks_pct = (delta_clicks / prev_clicks * 100) if prev_clicks > 0 else 0
        
        prompt = f"""DAY-OVER-DAY TREND ANALYSIS for {account_name}

PREVIOUS DAY: ₹{prev_spend:,.2f} | {prev_impressions:,} imp | {prev_clicks:,} clicks
YESTERDAY: ₹{curr_spend:,.2f} | {curr_impressions:,} imp | {curr_clicks:,} clicks
CHANGE: {delta_spend:+,.2f} ({delta_spend_pct:+.1f}%) spend | {delta_impressions:+,} ({delta_impressions_pct:+.1f}%) imp | {delta_clicks:+,} ({delta_clicks_pct:+.1f}%) clicks

SLACK FORMATTING:
• Use *bold* NOT ## or **
• Use • for bullets

Provide in this format:

*📊 WHAT CHANGED*
• Biggest shift in performance (good or bad)
• Is this a pattern or anomaly?
• Root cause analysis

*🚀 MOMENTUM PLAYS*
• What's accelerating? (campaigns gaining traction)
• Should we increase budgets? (where and by how much)
• What to replicate from winning campaigns

*🛑 DETERIORATING ASSETS*
• What's declining? (campaigns losing efficiency)
• Is this recoverable or should we kill it?
• Estimated money saved by pausing

*⚡ IMMEDIATE COURSE CORRECTIONS*
1. [Specific action with exact budget amounts]
2. [Creative/audience changes needed]
3. [Timeline for next check-in]

*🔮 TRAJECTORY*
• If this trend continues for 7 days, what happens?
• Critical threshold to watch (spend, CPI, CTR)

Be SPECIFIC. Use exact campaign names and numbers."""
        
        return prompt

