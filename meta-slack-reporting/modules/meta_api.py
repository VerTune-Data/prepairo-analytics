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

    def __init__(self, account_id: str, access_token: str, platforms: str = None):
        self.account_id = account_id
        self.access_token = access_token
        self.platforms = self._parse_platforms(platforms) if platforms else None
        FacebookAdsApi.init(access_token=access_token)
        self.ad_account = AdAccount(account_id)

    def _parse_platforms(self, platforms_str: str) -> List[str]:
        """Parse comma-separated platforms string into list"""
        if not platforms_str:
            return None
        return [p.strip().lower() for p in platforms_str.split(',')]

    def _filter_by_platform(self, insights_data: List[Dict], level: str) -> List[Dict]:
        """Filter insights by configured platforms"""
        if not self.platforms or not insights_data:
            return insights_data

        try:
            from facebook_business.adobjects.campaign import Campaign
            from facebook_business.adobjects.adset import AdSet

            # Build map of campaign/adset IDs to their publisher platforms
            platform_map = {}

            # Collect unique campaign/adset IDs
            ids_to_check = set()
            for insight in insights_data:
                if level == 'campaign':
                    campaign_id = insight.get('campaign_id')
                    if campaign_id:
                        ids_to_check.add(campaign_id)
                elif level in ['adset', 'ad']:
                    # For adsets and ads, we need to check the adset's publisher_platforms
                    adset_id = insight.get('adset_id')
                    if adset_id:
                        ids_to_check.add(adset_id)

            # Fetch publisher_platforms for each ID
            for obj_id in ids_to_check:
                try:
                    if level == 'campaign':
                        obj = Campaign(obj_id).api_get(fields=['publisher_platforms'])
                        platforms = obj.get('publisher_platforms', [])
                    else:
                        obj = AdSet(obj_id).api_get(fields=['publisher_platforms'])
                        platforms = obj.get('publisher_platforms', [])

                    # Normalize platform names to lowercase
                    platform_map[obj_id] = [p.lower() for p in platforms]
                except Exception as e:
                    logger.warning(f"Could not fetch platforms for {obj_id}: {e}")
                    platform_map[obj_id] = []

            # Filter insights based on platform
            filtered_insights = []
            for insight in insights_data:
                if level == 'campaign':
                    obj_id = insight.get('campaign_id')
                else:
                    obj_id = insight.get('adset_id')

                obj_platforms = platform_map.get(obj_id, [])

                # Check if any of the object's platforms match our filter
                if any(p in self.platforms for p in obj_platforms):
                    filtered_insights.append(insight)
                else:
                    logger.debug(f"Filtered out {level} {obj_id} with platforms {obj_platforms}")

            logger.info(f"Platform filtering: {len(insights_data)} -> {len(filtered_insights)} records (keeping only {self.platforms})")
            return filtered_insights

        except Exception as e:
            logger.error(f"Error filtering by platform: {e}")
            return insights_data

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

            # Filter by platform if configured
            insights_data = self._filter_by_platform(insights_data, level)

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

            # Filter by platform if configured
            insights_data = self._filter_by_platform(insights_data, level)

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
        """Fetch current ad account balance and spending limits"""
        try:
            logger.info(f"Fetching account balance for {self.account_id}")

            account_info = self.ad_account.api_get(
                fields=['account_id', 'balance', 'currency', 'spend_cap', 'amount_spent']
            )

            # Meta returns values in cents, convert to currency units
            balance_cents = float(account_info.get('balance', 0))
            balance = balance_cents / 100

            spend_cap_cents = float(account_info.get('spend_cap', 0))
            spend_cap = spend_cap_cents / 100

            amount_spent_cents = float(account_info.get('amount_spent', 0))
            amount_spent = amount_spent_cents / 100

            # Calculate remaining budget
            remaining_budget = spend_cap - amount_spent

            currency = account_info.get('currency', 'INR')
            currency_symbol = '₹' if currency == 'INR' else currency

            result = {
                'account_id': account_info.get('account_id', ''),
                'balance': balance,
                'spend_cap': spend_cap,
                'amount_spent': amount_spent,
                'remaining_budget': remaining_budget,
                'currency': currency,
                'balance_formatted': f"{currency_symbol}{remaining_budget:,.2f} available (of {currency_symbol}{spend_cap:,.2f} cap)"
            }

            logger.info(f"Remaining budget: {currency_symbol}{remaining_budget:,.2f} | Prepaid: {currency_symbol}{balance:,.2f}")
            return result

        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            return {
                'account_id': self.account_id,
                'balance': 0,
                'spend_cap': 0,
                'amount_spent': 0,
                'remaining_budget': 0,
                'currency': 'INR',
                'balance_formatted': '₹0.00 available'
            }
