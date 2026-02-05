"""
Meta Ads API wrapper for fetching today's cumulative insights
"""

import logging
from datetime import datetime
from typing import Dict, List
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

logger = logging.getLogger(__name__)


class MetaAdsAPIClient:
    """Wrapper for Meta Ads API with conversion tracking"""
    
    def __init__(self, account_id: str, access_token: str):
        self.account_id = account_id
        self.access_token = access_token
        FacebookAdsApi.init(access_token=access_token)
        self.ad_account = AdAccount(account_id)
    
    def fetch_todays_insights(self, level='campaign') -> List[Dict]:
        """
        Fetch today's cumulative insights (from midnight to now)
        Level can be: 'campaign', 'adset', or 'ad'
        """
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"Fetching {level}-level insights for today ({today})")
            
            params = {
                'time_range': {
                    'since': today,
                    'until': today
                },
                'level': level,
                'fields': [
                    'campaign_name',
                    'campaign_id',
                    'adset_name',
                    'adset_id',
                    'ad_name',
                    'ad_id',
                    'impressions',
                    'reach',
                    'spend',
                    'clicks',
                    'cpc',
                    'cpm',
                    'ctr',
                    'actions',
                    'cost_per_action_type',
                    'conversions',
                    'cost_per_conversion'
                ]
            }
            
            insights = self.ad_account.get_insights(params=params)
            insights_data = []
            
            for insight in insights:
                data = dict(insight)
                # Extract and add conversion actions
                data['parsed_actions'] = self.extract_actions(data)
                insights_data.append(data)
            
            logger.info(f"Fetched {len(insights_data)} {level}-level records for today")
            return insights_data
        
        except Exception as e:
            logger.error(f"Error fetching {level}-level insights: {e}")
            return []
    
    def extract_actions(self, insight: Dict) -> Dict:
        """Extract conversion actions from insight data"""
        actions = {}
        
        # Extract action counts
        action_list = insight.get('actions', [])
        for action in action_list:
            action_type = action.get('action_type', '')
            value = int(action.get('value', 0))
            actions[action_type] = value
        
        # Extract cost per action
        cost_per_action_list = insight.get('cost_per_action_type', [])
        for cpa in cost_per_action_list:
            action_type = cpa.get('action_type', '')
            cost = float(cpa.get('value', 0))
            actions[f"{action_type}_cost"] = cost
        
        return actions
    
    def fetch_account_balance(self) -> Dict:
        """Fetch current ad account balance"""
        try:
            logger.info(f"Fetching account balance for {self.account_id}")
            
            account_info = self.ad_account.api_get(
                fields=['account_id', 'balance', 'currency']
            )
            
            # Meta returns balance in cents, convert to currency units
            balance_cents = float(account_info.get('balance', 0))
            balance = balance_cents / 100
            currency = account_info.get('currency', 'INR')
            
            result = {
                'account_id': account_info.get('account_id', ''),
                'balance': balance,
                'currency': currency,
                'balance_formatted': f"{currency} {balance:,.2f}"
            }
            
            logger.info(f"Account balance: {result['balance_formatted']}")
            return result
        
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            return {
                'account_id': self.account_id,
                'balance': 0,
                'currency': 'INR',
                'balance_formatted': 'INR 0.00'
            }
