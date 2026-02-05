"""
Meta Ads API wrapper for fetching today's cumulative insights
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
import pytz
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

    def fetch_yesterday_insights(self, level='campaign') -> List[Dict]:
        """
        Fetch YESTERDAY's complete data (00:00 to 23:59 IST)
        Level can be: 'campaign', 'adset', or 'ad'
        """
        try:
            # Get yesterday's date in IST
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            yesterday_ist = now_ist - timedelta(days=1)
            yesterday_date = yesterday_ist.strftime('%Y-%m-%d')

            logger.info(f"Fetching {level}-level insights for YESTERDAY ({yesterday_date} IST)")

            params = {
                'time_range': {
                    'since': yesterday_date,
                    'until': yesterday_date
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

            logger.info(f"Fetched {len(insights_data)} {level}-level records for yesterday")

            # Fetch and merge status information
            insights_data = self._add_status_info(insights_data, level)

            return insights_data

        except Exception as e:
            logger.error(f"Error fetching {level}-level insights for yesterday: {e}")
            return []

    def _add_status_info(self, insights_data: List[Dict], level: str) -> List[Dict]:
        """Fetch status information and merge with insights data"""
        try:
            if not insights_data:
                return insights_data

            # Build map of IDs to fetch
            ids_to_fetch = set()
            for insight in insights_data:
                if level == 'campaign':
                    campaign_id = insight.get('campaign_id')
                    if campaign_id:
                        ids_to_fetch.add(campaign_id)
                elif level == 'adset':
                    adset_id = insight.get('adset_id')
                    if adset_id:
                        ids_to_fetch.add(adset_id)
                elif level == 'ad':
                    ad_id = insight.get('ad_id')
                    if ad_id:
                        ids_to_fetch.add(ad_id)

            if not ids_to_fetch:
                return insights_data

            # Fetch status for all IDs
            status_map = {}
            for obj_id in ids_to_fetch:
                try:
                    from facebook_business.adobjects.campaign import Campaign
                    from facebook_business.adobjects.adset import AdSet
                    from facebook_business.adobjects.ad import Ad

                    if level == 'campaign':
                        obj = Campaign(obj_id).api_get(fields=['effective_status'])
                    elif level == 'adset':
                        obj = AdSet(obj_id).api_get(fields=['effective_status'])
                    elif level == 'ad':
                        obj = Ad(obj_id).api_get(fields=['effective_status'])

                    status_map[obj_id] = obj.get('effective_status', 'UNKNOWN')
                except Exception as e:
                    logger.warning(f"Could not fetch status for {level} {obj_id}: {e}")
                    status_map[obj_id] = 'UNKNOWN'

            # Merge status back into insights
            for insight in insights_data:
                if level == 'campaign':
                    obj_id = insight.get('campaign_id')
                elif level == 'adset':
                    obj_id = insight.get('adset_id')
                elif level == 'ad':
                    obj_id = insight.get('ad_id')

                if obj_id in status_map:
                    insight['effective_status'] = status_map[obj_id]
                else:
                    insight['effective_status'] = 'UNKNOWN'

            logger.info(f"Added status information for {len(status_map)} {level}s")
            return insights_data

        except Exception as e:
            logger.error(f"Error adding status info: {e}")
            # Return data without status if there's an error
            for insight in insights_data:
                insight['effective_status'] = 'UNKNOWN'
            return insights_data

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
