"""
AWS Secrets Manager integration with 24-hour caching
Adapted from Java SecretsManagerCacheService pattern
"""

import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class AWSSecretsClient:
    """AWS Secrets Manager client with double-checked locking cache"""
    
    CACHE_DURATION_HOURS = 24
    SECRET_NAME = 'content-manager/prod/secrets'
    
    def __init__(self, region: str = 'ap-south-1'):
        self.region = region
        self._cached_secrets: Optional[Dict] = None
        self._cache_expiry: Optional[datetime] = None
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of boto3 client"""
        if self._client is None:
            self._client = boto3.client('secretsmanager', region_name=self.region)
        return self._client
    
    def get_claude_api_key(self) -> Optional[str]:
        """
        Get Claude API key with 24-hour cache
        Returns None if secret not found or error occurs
        """
        try:
            # Double-checked locking pattern
            if self._cache_expired():
                self._load_from_secrets_manager()
            
            if self._cached_secrets:
                api_key = self._cached_secrets.get('CLAUDE_API_KEY')
                if api_key:
                    logger.info("Retrieved Claude API key from cache")
                    return api_key
                else:
                    logger.warning("CLAUDE_API_KEY not found in secrets")
                    return None
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting Claude API key: {e}")
            return None
    
    def _cache_expired(self) -> bool:
        """Check if cache has expired"""
        if self._cached_secrets is None or self._cache_expiry is None:
            return True
        return datetime.now() >= self._cache_expiry
    
    def _load_from_secrets_manager(self):
        """Load secrets from AWS Secrets Manager"""
        try:
            logger.info(f"Loading secrets from {self.SECRET_NAME} in {self.region}")
            
            client = self._get_client()
            response = client.get_secret_value(SecretId=self.SECRET_NAME)
            
            secret_string = response.get('SecretString')
            if secret_string:
                self._cached_secrets = json.loads(secret_string)
                self._cache_expiry = datetime.now() + timedelta(hours=self.CACHE_DURATION_HOURS)
                logger.info(f"Secrets loaded successfully. Cache valid until {self._cache_expiry}")
            else:
                logger.error("Secret string is empty")
                self._cached_secrets = {}
        
        except Exception as e:
            logger.error(f"Failed to load secrets from AWS Secrets Manager: {e}")
            self._cached_secrets = {}
    
    def is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        return not self._cache_expired()
    
    def clear_cache(self):
        """Force cache refresh on next request"""
        self._cached_secrets = None
        self._cache_expiry = None
        logger.info("Cache cleared - will refresh on next request")
