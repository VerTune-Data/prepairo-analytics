"""
AI Campaign Analyzer - Adds observation, recommendation, action, reason columns
Uses Claude to analyze each campaign/adset/ad and provide actionable insights
"""

import logging
from typing import List, Dict
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AICampaignAnalyzer:
    """Analyze campaigns with AI to add observation/recommendation/action/reason columns"""

    def __init__(self, api_key: str, model: str = 'claude-sonnet-4-5-20250929'):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def analyze_campaigns(self, campaigns: List[Dict]) -> List[Dict]:
        """
        Analyze campaigns and add AI columns:
        - ai_observation: What's happening
        - ai_recommendation: What to do
        - ai_action: Pause/Continue/Scale
        - ai_reason: Why this action
        """
        if not campaigns:
            return campaigns

        try:
            # Build prompt with all campaigns
            prompt = self._build_campaign_analysis_prompt(campaigns)

            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text

            # Parse response and add AI columns to campaigns
            enriched_campaigns = self._parse_and_enrich(campaigns, analysis_text)

            logger.info(f"AI analysis completed for {len(enriched_campaigns)} campaigns")
            return enriched_campaigns

        except Exception as e:
            logger.error(f"AI campaign analysis failed: {e}")
            # Return campaigns with default AI columns
            for campaign in campaigns:
                campaign['ai_observation'] = "Analysis unavailable"
                campaign['ai_recommendation'] = "Manual review needed"
                campaign['ai_action'] = "Continue"
                campaign['ai_reason'] = f"AI analysis error: {str(e)[:50]}"
            return campaigns

    def _build_campaign_analysis_prompt(self, campaigns: List[Dict]) -> str:
        """Build prompt for campaign analysis"""
        prompt = """You are a Meta Ads performance marketing expert. Analyze each campaign and provide:
1. **Observation**: What's happening with this campaign (1 sentence)
2. **Recommendation**: What action to take (1 sentence)
3. **Action**: One of: Continue, Pause, Scale Up, Review
4. **Reason**: Why this action is recommended (1 sentence)

Format your response EXACTLY like this for each campaign:
---
CAMPAIGN: [name]
OBSERVATION: [one sentence observation]
RECOMMENDATION: [one sentence recommendation]
ACTION: [Continue/Pause/Scale Up/Review]
REASON: [one sentence reason]
---

Here are the campaigns to analyze:

"""

        for i, campaign in enumerate(campaigns[:15], 1):  # Analyze top 15
            name = campaign.get('campaign_name', 'Unknown')
            spend = float(campaign.get('spend', 0))
            impressions = int(campaign.get('impressions', 0))
            clicks = int(campaign.get('clicks', 0))
            ctr = float(campaign.get('ctr', 0))
            status = campaign.get('effective_status', 'UNKNOWN')

            # Get conversions
            parsed = campaign.get('parsed_actions', {})
            installs = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or 0)
            registrations = int(parsed.get('omni_complete_registration', 0) or 0)
            purchases = int(parsed.get('omni_purchase', 0) or 0)

            # Calculate costs
            cpi = (spend / installs) if installs > 0 else 0
            cpr = (spend / registrations) if registrations > 0 else 0
            cpa = (spend / purchases) if purchases > 0 else 0

            prompt += f"""
{i}. Campaign: {name}
   Status: {status}
   Spend: ₹{spend:,.0f}
   Impressions: {impressions:,}
   Clicks: {clicks:,}
   CTR: {ctr:.2f}%
   Installs: {installs} (CPI: ₹{cpi:.0f})
   Registrations: {registrations} (CPR: ₹{cpr:.0f})
   Purchases: {purchases} (CPA: ₹{cpa:.0f})
"""

        prompt += """

Consider:
- CPI > ₹100 is high (recommend pause/review)
- CTR < 1% is low (needs optimization)
- Zero conversions with high spend (pause immediately)
- Good CPI + high volume (scale up)
- Paused campaigns with good metrics (recommend re-enabling)

Provide analysis for ALL campaigns listed above."""

        return prompt

    def _parse_and_enrich(self, campaigns: List[Dict], analysis_text: str) -> List[Dict]:
        """Parse AI response and add columns to campaigns"""
        # Split by campaign sections
        sections = analysis_text.split('---')

        # Build a mapping from campaign names to analysis
        analysis_map = {}

        for section in sections:
            if 'CAMPAIGN:' not in section:
                continue

            try:
                lines = [l.strip() for l in section.strip().split('\n') if l.strip()]

                campaign_line = [l for l in lines if l.startswith('CAMPAIGN:')][0]
                campaign_name = campaign_line.replace('CAMPAIGN:', '').strip()

                observation = [l for l in lines if l.startswith('OBSERVATION:')]
                observation = observation[0].replace('OBSERVATION:', '').strip() if observation else "Normal"

                recommendation = [l for l in lines if l.startswith('RECOMMENDATION:')]
                recommendation = recommendation[0].replace('RECOMMENDATION:', '').strip() if recommendation else "Monitor"

                action = [l for l in lines if l.startswith('ACTION:')]
                action = action[0].replace('ACTION:', '').strip() if action else "Continue"

                reason = [l for l in lines if l.startswith('REASON:')]
                reason = reason[0].replace('REASON:', '').strip() if reason else "Normal performance"

                analysis_map[campaign_name] = {
                    'observation': observation,
                    'recommendation': recommendation,
                    'action': action,
                    'reason': reason
                }

            except Exception as e:
                logger.warning(f"Failed to parse section: {e}")
                continue

        # Add AI columns to campaigns
        for campaign in campaigns:
            name = campaign.get('campaign_name', '')
            if name in analysis_map:
                analysis = analysis_map[name]
                campaign['ai_observation'] = analysis['observation']
                campaign['ai_recommendation'] = analysis['recommendation']
                campaign['ai_action'] = analysis['action']
                campaign['ai_reason'] = analysis['reason']
            else:
                # Default values if not found in AI response
                campaign['ai_observation'] = "Needs review"
                campaign['ai_recommendation'] = "Manual analysis required"
                campaign['ai_action'] = "Continue"
                campaign['ai_reason'] = "Analysis not available"

        return campaigns

    def analyze_adsets(self, adsets: List[Dict]) -> List[Dict]:
        """Analyze adsets and add AI columns"""
        if not adsets:
            return adsets

        try:
            prompt = self._build_adset_analysis_prompt(adsets)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text
            enriched_adsets = self._parse_and_enrich_adsets(adsets, analysis_text)

            logger.info(f"AI analysis completed for {len(enriched_adsets)} adsets")
            return enriched_adsets

        except Exception as e:
            logger.error(f"AI adset analysis failed: {e}")
            for adset in adsets:
                adset['ai_observation'] = "Performance tracking"
                adset['ai_recommendation'] = "Monitor closely"
                adset['ai_action'] = "Continue"
                adset['ai_reason'] = f"AI analysis error: {str(e)[:50]}"
            return adsets

    def _build_adset_analysis_prompt(self, adsets: List[Dict]) -> str:
        """Build prompt for adset analysis"""
        prompt = """You are a Meta Ads expert. Analyze each adset and provide:
1. **Observation**: What's happening (1 sentence)
2. **Recommendation**: What action to take (1 sentence)
3. **Action**: One of: Continue, Pause, Scale Up, Review
4. **Reason**: Why this action (1 sentence)

Format EXACTLY like this for each adset:
---
ADSET: [name]
OBSERVATION: [one sentence]
RECOMMENDATION: [one sentence]
ACTION: [Continue/Pause/Scale Up/Review]
REASON: [one sentence]
---

Here are the adsets to analyze:

"""
        for i, adset in enumerate(adsets[:20], 1):  # Top 20
            name = adset.get('adset_name', 'Unknown')
            campaign = adset.get('campaign_name', 'Unknown')
            spend = float(adset.get('spend', 0))
            impressions = int(adset.get('impressions', 0))
            clicks = int(adset.get('clicks', 0))
            ctr = float(adset.get('ctr', 0))
            status = adset.get('effective_status', 'UNKNOWN')

            parsed = adset.get('parsed_actions', {})
            installs = int(parsed.get('omni_app_install', 0) or 0)
            registrations = int(parsed.get('omni_complete_registration', 0) or 0)
            purchases = int(parsed.get('omni_purchase', 0) or 0)

            cpi = (spend / installs) if installs > 0 else 0
            cpr = (spend / registrations) if registrations > 0 else 0
            cpa = (spend / purchases) if purchases > 0 else 0

            prompt += f"""
{i}. AdSet: {name}
   Campaign: {campaign}
   Status: {status}
   Spend: ₹{spend:,.0f}
   Impressions: {impressions:,}
   Clicks: {clicks:,} | CTR: {ctr:.2f}%
   Installs: {installs} (CPI: ₹{cpi:.0f})
   Registrations: {registrations} (CPR: ₹{cpr:.0f})
   Purchases: {purchases} (CPA: ₹{cpa:.0f})
"""

        prompt += """

Consider:
- CPI > ₹100 is high (recommend pause/review)
- CTR < 1% is low (needs optimization)
- Zero conversions with high spend (pause immediately)
- Good CPI + high volume (scale up)
- Compare performance within same campaign

Provide analysis for ALL adsets listed above."""

        return prompt

    def _parse_and_enrich_adsets(self, adsets: List[Dict], analysis_text: str) -> List[Dict]:
        """Parse AI response and add columns to adsets"""
        sections = analysis_text.split('---')
        analysis_map = {}

        for section in sections:
            if 'ADSET:' not in section:
                continue

            try:
                lines = [l.strip() for l in section.strip().split('\n') if l.strip()]

                adset_line = [l for l in lines if l.startswith('ADSET:')][0]
                adset_name = adset_line.replace('ADSET:', '').strip()

                observation = [l for l in lines if l.startswith('OBSERVATION:')]
                observation = observation[0].replace('OBSERVATION:', '').strip() if observation else "Normal"

                recommendation = [l for l in lines if l.startswith('RECOMMENDATION:')]
                recommendation = recommendation[0].replace('RECOMMENDATION:', '').strip() if recommendation else "Monitor"

                action = [l for l in lines if l.startswith('ACTION:')]
                action = action[0].replace('ACTION:', '').strip() if action else "Continue"

                reason = [l for l in lines if l.startswith('REASON:')]
                reason = reason[0].replace('REASON:', '').strip() if reason else "Normal performance"

                analysis_map[adset_name] = {
                    'observation': observation,
                    'recommendation': recommendation,
                    'action': action,
                    'reason': reason
                }

            except Exception as e:
                logger.warning(f"Failed to parse adset section: {e}")
                continue

        for adset in adsets:
            name = adset.get('adset_name', '')
            if name in analysis_map:
                analysis = analysis_map[name]
                adset['ai_observation'] = analysis['observation']
                adset['ai_recommendation'] = analysis['recommendation']
                adset['ai_action'] = analysis['action']
                adset['ai_reason'] = analysis['reason']
            else:
                adset['ai_observation'] = "Performance tracking"
                adset['ai_recommendation'] = "Monitor closely"
                adset['ai_action'] = "Continue"
                adset['ai_reason'] = "Analysis not available"

        return adsets

    def analyze_ads(self, ads: List[Dict]) -> List[Dict]:
        """Analyze ads and add AI columns"""
        if not ads:
            return ads

        try:
            prompt = self._build_ad_analysis_prompt(ads)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text
            enriched_ads = self._parse_and_enrich_ads(ads, analysis_text)

            logger.info(f"AI analysis completed for {len(enriched_ads)} ads")
            return enriched_ads

        except Exception as e:
            logger.error(f"AI ad analysis failed: {e}")
            for ad in ads:
                ad['ai_observation'] = "Active delivery"
                ad['ai_recommendation'] = "Keep running"
                ad['ai_action'] = "Continue"
                ad['ai_reason'] = f"AI analysis error: {str(e)[:50]}"
            return ads

    def _build_ad_analysis_prompt(self, ads: List[Dict]) -> str:
        """Build prompt for ad analysis"""
        prompt = """You are a Meta Ads creative expert. Analyze each ad and provide:
1. **Observation**: What's happening (1 sentence)
2. **Recommendation**: What action to take (1 sentence)
3. **Action**: One of: Continue, Pause, Test New Creative, Review
4. **Reason**: Why this action (1 sentence)

Format EXACTLY like this for each ad:
---
AD: [name]
OBSERVATION: [one sentence]
RECOMMENDATION: [one sentence]
ACTION: [Continue/Pause/Test New Creative/Review]
REASON: [one sentence]
---

Here are the ads to analyze:

"""
        for i, ad in enumerate(ads[:25], 1):  # Top 25
            name = ad.get('ad_name', 'Unknown')
            adset = ad.get('adset_name', 'Unknown')
            spend = float(ad.get('spend', 0))
            impressions = int(ad.get('impressions', 0))
            clicks = int(ad.get('clicks', 0))
            ctr = float(ad.get('ctr', 0))
            status = ad.get('effective_status', 'UNKNOWN')

            parsed = ad.get('parsed_actions', {})
            installs = int(parsed.get('omni_app_install', 0) or 0)
            cpi = (spend / installs) if installs > 0 else 0

            prompt += f"""
{i}. Ad: {name}
   AdSet: {adset}
   Status: {status}
   Spend: ₹{spend:,.0f}
   Impressions: {impressions:,}
   Clicks: {clicks:,} | CTR: {ctr:.2f}%
   Installs: {installs} (CPI: ₹{cpi:.0f})
"""

        prompt += """

Consider:
- CTR < 0.8% indicates poor creative performance
- Zero clicks with high impressions = creative fatigue
- High CTR but no conversions = landing page issue
- Compare performance within same adset
- High spend with poor metrics = pause immediately

Provide analysis for ALL ads listed above."""

        return prompt

    def _parse_and_enrich_ads(self, ads: List[Dict], analysis_text: str) -> List[Dict]:
        """Parse AI response and add columns to ads"""
        sections = analysis_text.split('---')
        analysis_map = {}

        for section in sections:
            if 'AD:' not in section:
                continue

            try:
                lines = [l.strip() for l in section.strip().split('\n') if l.strip()]

                ad_line = [l for l in lines if l.startswith('AD:')][0]
                ad_name = ad_line.replace('AD:', '').strip()

                observation = [l for l in lines if l.startswith('OBSERVATION:')]
                observation = observation[0].replace('OBSERVATION:', '').strip() if observation else "Active delivery"

                recommendation = [l for l in lines if l.startswith('RECOMMENDATION:')]
                recommendation = recommendation[0].replace('RECOMMENDATION:', '').strip() if recommendation else "Keep running"

                action = [l for l in lines if l.startswith('ACTION:')]
                action = action[0].replace('ACTION:', '').strip() if action else "Continue"

                reason = [l for l in lines if l.startswith('REASON:')]
                reason = reason[0].replace('REASON:', '').strip() if reason else "Normal metrics"

                analysis_map[ad_name] = {
                    'observation': observation,
                    'recommendation': recommendation,
                    'action': action,
                    'reason': reason
                }

            except Exception as e:
                logger.warning(f"Failed to parse ad section: {e}")
                continue

        for ad in ads:
            name = ad.get('ad_name', '')
            if name in analysis_map:
                analysis = analysis_map[name]
                ad['ai_observation'] = analysis['observation']
                ad['ai_recommendation'] = analysis['recommendation']
                ad['ai_action'] = analysis['action']
                ad['ai_reason'] = analysis['reason']
            else:
                ad['ai_observation'] = "Active delivery"
                ad['ai_recommendation'] = "Keep running"
                ad['ai_action'] = "Continue"
                ad['ai_reason'] = "Analysis not available"

        return ads
