"""
Claude AI analyzer with Slack-compatible formatting
"""

import logging
from typing import Dict, Optional, Tuple
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
        Analyze current 8-hour window with Slack formatting
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
                trend_analysis = "⏳ No previous data - trend analysis will be available in next report (8 hours)"
            
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
            camp_imp = int(camp.get('impressions', 0))
            camp_clicks = int(camp.get('clicks', 0))
            
            camp_detail = f"Campaign: {camp_name}\n"
            camp_detail += f"  Spend: ₹{camp_spend:,.2f} | Impressions: {camp_imp:,} | Clicks: {camp_clicks}\n"
            
            camp_adsets = [a for a in adsets if a.get('campaign_id') == camp_id]
            if camp_adsets:
                camp_detail += f"  AdSets ({len(camp_adsets)}):\n"
                for adset in sorted(camp_adsets, key=lambda x: float(x.get('spend', 0)), reverse=True):
                    adset_id = adset.get('adset_id')
                    adset_name = adset.get('adset_name', 'Unknown')[:35]
                    adset_spend = float(adset.get('spend', 0))
                    camp_detail += f"    - {adset_name}: ₹{adset_spend:,.2f}\n"
                    
                    adset_ads = [a for a in ads if a.get('adset_id') == adset_id]
                    for ad in sorted(adset_ads, key=lambda x: float(x.get('spend', 0)), reverse=True):
                        ad_name = ad.get('ad_name', 'Unknown')[:30]
                        ad_spend = float(ad.get('spend', 0))
                        ad_clicks = int(ad.get('clicks', 0))
                        camp_detail += f"      • {ad_name}: ₹{ad_spend:,.2f} | {ad_clicks} clicks\n"
            
            detailed_breakdown.append(camp_detail)
        
        prompt = f"""You are a Meta Ads analyst for {account_name}. Provide actionable insights.

DATA:
{chr(10).join(detailed_breakdown)}
Balance: {balance.get('balance_formatted', '₹0.00')}

IMPORTANT FORMATTING RULES FOR SLACK:
- Use *bold* for emphasis (NOT ** or ##)
- Use • for bullets (NOT - or *)
- NO markdown headings (##, ###) - use *SECTION NAME* instead
- Keep formatting simple and Slack-compatible
- Use emojis for visual breaks

Provide insights in this EXACT format:

*📊 Performance Overview*
• Overall account health assessment
• Key efficiency metrics (CTR, CPI trends)

*🏆 Top Performers*
• Best campaign/adset/ad and why
• What's working well

*⚠️ Underperformers*
• Worst performing elements
• Specific problems identified

*💡 Immediate Actions*
1. Specific action with exact amounts
2. Which ads to pause
3. Budget reallocation suggestions

*💰 Budget Status*
• Days remaining at current spend
• Top-up urgency level

Keep each point to 1-2 lines max. Be specific with numbers."""
        
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
        
        prompt = f"""Analyze 8-HOUR TRENDS for {account_name}.

PREVIOUS: ₹{prev_spend:,.2f} | {prev_impressions:,} imp | {prev_clicks:,} clicks
CURRENT: ₹{curr_spend:,.2f} | {curr_impressions:,} imp | {curr_clicks:,} clicks
DELTAS: {delta_spend:+,.2f} ({delta_spend_pct:+.1f}%) | {delta_impressions:+,} ({delta_impressions_pct:+.1f}%) | {delta_clicks:+,} ({delta_clicks_pct:+.1f}%)

SLACK FORMATTING RULES:
- Use *bold* NOT ## or **
- Use • for bullets
- Keep it simple

Provide in this format:

*📈 Key Changes*
• What changed most and why
• Is this positive or concerning?

*🎯 Efficiency Trends*
• CTR/CPI movement
• What's driving the change

*⚠️ Red Flags*
• Urgent issues requiring immediate action
• Timeline to crisis if trend continues

*✅ Positive Momentum*
• What to double down on

*🔮 Predictions*
• Expected outcome if trend continues
• Recommended course corrections

Keep concise. Be specific."""
        
        return prompt

