"""
Delta calculator for comparing current and previous snapshots
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DeltaCalculator:
    """Calculate deltas between current and previous snapshots"""
    
    def calculate_deltas(self, current_data: Dict, previous_data: Dict) -> Dict:
        """
        Compare current and previous snapshots
        Returns structured delta information
        """
        try:
            # Account-level deltas
            account_deltas = self._calculate_account_deltas(current_data, previous_data)
            
            # Campaign-level deltas
            campaign_deltas = self._calculate_campaign_deltas(
                current_data.get('campaigns', []),
                previous_data.get('campaigns', [])
            )
            
            # Find significant changes (>20% change)
            significant_changes = self._identify_significant_changes(campaign_deltas)
            
            return {
                'account': account_deltas,
                'campaigns': campaign_deltas,
                'adsets': [],  # TODO: Add if needed
                'ads': [],     # TODO: Add if needed
                'significant_changes': significant_changes
            }
        
        except Exception as e:
            logger.error(f"Error calculating deltas: {e}")
            return {'account': {}, 'campaigns': [], 'significant_changes': []}
    
    def _calculate_account_deltas(self, current: Dict, previous: Dict) -> Dict:
        """Calculate account-level deltas"""
        curr_campaigns = current.get('campaigns', [])
        prev_campaigns = previous.get('campaigns', [])
        
        # Aggregate totals
        curr_spend = sum(float(c.get('spend', 0)) for c in curr_campaigns)
        curr_impressions = sum(int(c.get('impressions', 0)) for c in curr_campaigns)
        curr_clicks = sum(int(c.get('clicks', 0)) for c in curr_campaigns)
        
        prev_spend = sum(float(c.get('spend', 0)) for c in prev_campaigns)
        prev_impressions = sum(int(c.get('impressions', 0)) for c in prev_campaigns)
        prev_clicks = sum(int(c.get('clicks', 0)) for c in prev_campaigns)
        
        return {
            'spend': self.calculate_metric_delta(curr_spend, prev_spend),
            'impressions': self.calculate_metric_delta(curr_impressions, prev_impressions),
            'clicks': self.calculate_metric_delta(curr_clicks, prev_clicks),
        }
    
    def _calculate_campaign_deltas(self, current_campaigns: List[Dict], previous_campaigns: List[Dict]) -> List[Dict]:
        """Calculate campaign-level deltas"""
        # Build previous campaigns lookup by campaign_id
        prev_lookup = {}
        for camp in previous_campaigns:
            camp_id = camp.get('campaign_id')
            if camp_id:
                prev_lookup[camp_id] = camp
        
        campaign_deltas = []
        for curr_camp in current_campaigns:
            camp_id = curr_camp.get('campaign_id')
            camp_name = curr_camp.get('campaign_name', 'Unknown')
            
            curr_spend = float(curr_camp.get('spend', 0))
            curr_impressions = int(curr_camp.get('impressions', 0))
            curr_clicks = int(curr_camp.get('clicks', 0))
            
            # Find previous data
            prev_camp = prev_lookup.get(camp_id, {})
            prev_spend = float(prev_camp.get('spend', 0))
            prev_impressions = int(prev_camp.get('impressions', 0))
            prev_clicks = int(prev_camp.get('clicks', 0))
            
            # Get conversions
            curr_actions = curr_camp.get('parsed_actions', {})
            prev_actions = prev_camp.get('parsed_actions', {})
            
            campaign_deltas.append({
                'campaign_id': camp_id,
                'name': camp_name,
                'spend': curr_spend,
                'impressions': curr_impressions,
                'clicks': curr_clicks,
                'conversions': curr_actions,
                'delta_spend': self.calculate_metric_delta(curr_spend, prev_spend),
                'delta_impressions': self.calculate_metric_delta(curr_impressions, prev_impressions),
                'delta_clicks': self.calculate_metric_delta(curr_clicks, prev_clicks),
                'prev_spend': prev_spend,
                'prev_impressions': prev_impressions,
                'prev_clicks': prev_clicks,
            })
        
        # Sort by current spend
        campaign_deltas.sort(key=lambda x: x['spend'], reverse=True)
        return campaign_deltas
    
    def calculate_metric_delta(self, current: float, previous: float) -> Dict:
        """Calculate absolute and percentage change"""
        delta = current - previous
        percent = (delta / previous * 100) if previous > 0 else 0
        
        return {
            'current': current,
            'previous': previous,
            'delta': delta,
            'percent': percent
        }
    
    def _identify_significant_changes(self, campaign_deltas: List[Dict], threshold: float = 20.0) -> List[Dict]:
        """Identify campaigns with >threshold% change"""
        significant = []
        
        for camp in campaign_deltas:
            delta_pct = camp['delta_spend']['percent']
            
            if abs(delta_pct) > threshold and camp['spend'] > 100:  # Only if spend > ₹100
                alert_type = 'large_increase' if delta_pct > 0 else 'large_decrease'
                significant.append({
                    'entity': camp['name'],
                    'metric': 'spend',
                    'change': delta_pct,
                    'alert': alert_type,
                    'current': camp['spend'],
                    'previous': camp['prev_spend']
                })
        
        return significant
    
    def format_delta_summary(self, deltas: Dict) -> str:
        """Format delta summary as readable text"""
        account = deltas.get('account', {})
        
        spend_delta = account.get('spend', {})
        imp_delta = account.get('impressions', {})
        clicks_delta = account.get('clicks', {})
        
        lines = [
            f"Spend: ₹{spend_delta.get('current', 0):,.2f} ({spend_delta.get('percent', 0):+.1f}%)",
            f"Impressions: {imp_delta.get('current', 0):,} ({imp_delta.get('percent', 0):+.1f}%)",
            f"Clicks: {clicks_delta.get('current', 0):,} ({clicks_delta.get('percent', 0):+.1f}%)"
        ]
        
        significant = deltas.get('significant_changes', [])
        if significant:
            lines.append("\nSignificant Changes:")
            for change in significant[:3]:  # Top 3
                emoji = "📈" if change['alert'] == 'large_increase' else "📉"
                lines.append(f"{emoji} {change['entity'][:30]}: {change['change']:+.1f}%")
        
        return "\n".join(lines)
