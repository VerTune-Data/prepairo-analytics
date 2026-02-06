"""
Table formatter for Slack - creates clean table views of campaign/adset/ad data
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class TableFormatter:
    """Format data as tables for Slack"""

    @staticmethod
    def format_campaign_table(campaigns: List[Dict], include_ai_columns: bool = True) -> str:
        """
        Format campaigns as a clean table
        Slack doesn't support true tables, so we use monospace formatting
        """
        if not campaigns:
            return "_No campaigns found_"

        lines = []
        lines.append("```")

        # Header
        if include_ai_columns:
            lines.append("Campaign                    | Spend    | Impr  | Clicks| CPI    | Action      | Reason")
            lines.append("-" * 110)
        else:
            lines.append("Campaign                    | Spend    | Impressions | Clicks | CPI")
            lines.append("-" * 75)

        # Rows
        for campaign in campaigns[:10]:  # Top 10
            name = campaign.get('campaign_name', 'Unknown')[:25].ljust(25)
            spend = f"₹{float(campaign.get('spend', 0)):,.0f}".rjust(8)
            impressions = f"{int(campaign.get('impressions', 0)):,}"[:6].rjust(6)
            clicks = f"{int(campaign.get('clicks', 0)):,}"[:6].rjust(6)

            # Calculate CPI
            parsed = campaign.get('parsed_actions', {})
            installs = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or 0)
            cpi = (float(campaign.get('spend', 0)) / installs) if installs > 0 else 0
            cpi_str = f"₹{cpi:.0f}".rjust(6)

            if include_ai_columns:
                action = campaign.get('ai_action', 'Continue')[:11].ljust(11)
                reason = campaign.get('ai_reason', 'Normal')[:30]
                line = f"{name} | {spend} | {impressions} | {clicks} | {cpi_str} | {action} | {reason}"
            else:
                line = f"{name} | {spend} | {impressions} | {clicks} | {cpi_str}"

            lines.append(line)

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def format_adset_table(adsets: List[Dict], campaign_name: str = None) -> str:
        """Format adsets as a table"""
        if not adsets:
            return "_No adsets found_"

        lines = []
        if campaign_name:
            lines.append(f"*AdSets for: {campaign_name}*")
        lines.append("```")

        # Header
        lines.append("AdSet                      | Spend   | Conv | CPI    | Status  | Action")
        lines.append("-" * 80)

        # Rows
        for adset in adsets[:15]:  # Top 15
            name = adset.get('adset_name', 'Unknown')[:24].ljust(24)
            spend = f"₹{float(adset.get('spend', 0)):,.0f}".rjust(7)

            # Get conversions
            parsed = adset.get('parsed_actions', {})
            conversions = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or 0)
            conv_str = str(conversions).rjust(4)

            # CPI
            cpi = (float(adset.get('spend', 0)) / conversions) if conversions > 0 else 0
            cpi_str = f"₹{cpi:.0f}".rjust(6)

            status = adset.get('effective_status', 'UNKNOWN')[:7].ljust(7)
            action = adset.get('ai_action', 'Continue')[:10]

            line = f"{name} | {spend} | {conv_str} | {cpi_str} | {status} | {action}"
            lines.append(line)

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def format_ad_table(ads: List[Dict], adset_name: str = None) -> str:
        """Format ads as a table"""
        if not ads:
            return "_No ads found_"

        lines = []
        if adset_name:
            lines.append(f"*Ads for: {adset_name}*")
        lines.append("```")

        # Header
        lines.append("Ad Name                    | Spend  | Conv | CTR   | Status  | Rec")
        lines.append("-" * 75)

        # Rows
        for ad in ads[:20]:  # Top 20
            name = ad.get('ad_name', 'Unknown')[:24].ljust(24)
            spend = f"₹{float(ad.get('spend', 0)):,.0f}".rjust(6)

            # Conversions
            parsed = ad.get('parsed_actions', {})
            conversions = int(parsed.get('omni_app_install', 0) or parsed.get('app_install', 0) or 0)
            conv_str = str(conversions).rjust(4)

            # CTR
            ctr = float(ad.get('ctr', 0))
            ctr_str = f"{ctr:.2f}%".rjust(5)

            status = ad.get('effective_status', 'UNKNOWN')[:7].ljust(7)
            rec = ad.get('ai_recommendation', 'OK')[:10]

            line = f"{name} | {spend} | {conv_str} | {ctr_str} | {status} | {rec}"
            lines.append(line)

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def format_summary_table(summary_data: Dict) -> str:
        """Format summary metrics as a compact table"""
        lines = []
        lines.append("```")
        lines.append("Metric          | Current    | Previous   | Change")
        lines.append("-" * 55)

        for metric, data in summary_data.items():
            metric_name = metric.capitalize()[:14].ljust(14)
            current = f"{data.get('current', 0):,.0f}".rjust(10)
            previous = f"{data.get('previous', 0):,.0f}".rjust(10)
            change_pct = data.get('percent', 0)
            change_str = f"{change_pct:+.1f}%".rjust(7)

            line = f"{metric_name} | {current} | {previous} | {change_str}"
            lines.append(line)

        lines.append("```")
        return "\n".join(lines)
