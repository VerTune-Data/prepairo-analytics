"""
Error handling utilities for Meta Ads API and reporting
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def handle_meta_api_error(error) -> str:
    """
    Translate Meta API errors to user-friendly messages

    Args:
        error: Exception from Meta API

    Returns:
        User-friendly error message
    """
    # Extract error code if available
    error_code = getattr(error, 'api_error_code', None)
    error_message = str(error)

    # Common Meta API error codes
    error_map = {
        190: "❌ Access token expired or invalid. Please regenerate your Meta access token.",
        17: "❌ API rate limit exceeded. Please wait 5-10 minutes and try again.",
        4: "❌ API rate limit exceeded. Too many requests. Wait and retry.",
        100: "❌ Invalid parameter in API request. Check your configuration.",
        80001: "❌ Invalid ad account ID. Verify META_ADS_ACCOUNT_ID in your .env file.",
        80004: "❌ Too many API calls. Please reduce request frequency.",
        2: "❌ API service temporarily unavailable. Try again in a few minutes.",
        1: "❌ API error: Unknown server error.",
    }

    if error_code in error_map:
        return error_map[error_code]

    # Check for common error patterns in message
    if 'access token' in error_message.lower():
        return "❌ Access token issue. Please check META_ACCESS_TOKEN in your .env file."
    elif 'rate limit' in error_message.lower():
        return "❌ API rate limit hit. Wait a few minutes before retrying."
    elif 'permission' in error_message.lower():
        return "❌ Permission denied. Ensure your access token has ads_read permission."
    elif 'account' in error_message.lower():
        return "❌ Ad account error. Verify META_ADS_ACCOUNT_ID is correct."

    # Generic fallback
    return f"❌ Meta API error: {error_message}"


def handle_slack_error(error, status_code: Optional[int] = None) -> str:
    """
    Translate Slack webhook errors to user-friendly messages

    Args:
        error: Exception from Slack request
        status_code: HTTP status code if available

    Returns:
        User-friendly error message
    """
    if status_code == 404:
        return "❌ Slack webhook URL not found. Verify SLACK_WEBHOOK_URL in your .env file."
    elif status_code == 400:
        return "❌ Invalid Slack message format. Contact support."
    elif status_code == 403:
        return "❌ Slack webhook access denied. Webhook may have been revoked."
    elif status_code == 500:
        return "❌ Slack service error. Try again in a few minutes."
    elif status_code and status_code >= 500:
        return "❌ Slack server error. Try again later."

    return f"❌ Slack webhook error: {str(error)}"


def handle_aws_error(error) -> str:
    """
    Translate AWS errors to user-friendly messages

    Args:
        error: Exception from AWS SDK

    Returns:
        User-friendly error message
    """
    error_message = str(error)

    if 'credentials' in error_message.lower():
        return "❌ AWS credentials not configured. Check AWS CLI setup."
    elif 'access denied' in error_message.lower():
        return "❌ AWS access denied. Verify IAM permissions for S3/Secrets Manager."
    elif 'bucket' in error_message.lower():
        return "❌ S3 bucket error. Check bucket name and permissions."
    elif 'secret' in error_message.lower():
        return "❌ AWS Secrets Manager error. Verify secret name and permissions."

    return f"❌ AWS error: {error_message}"


def format_validation_error(field_name: str, expected: str) -> str:
    """
    Format validation error message

    Args:
        field_name: Name of the field that failed validation
        expected: Description of expected value

    Returns:
        Formatted error message
    """
    return f"❌ Invalid {field_name}: {expected}"
