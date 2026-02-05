"""
Configuration loader for multi-account Meta Ads management
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


def load_account_config(account_name: str) -> dict:
    """
    Load configuration for specified account

    Args:
        account_name: Account identifier ('gre', 'upsc', or 'test')

    Returns:
        Dictionary with all configuration values

    Raises:
        ConfigurationError: If config file not found or required values missing
    """
    # Determine config file path
    if account_name == 'gre':
        env_file = Path(__file__).parent.parent / '.env'
    else:
        env_file = Path(__file__).parent.parent / f'.env.{account_name}'

    if not env_file.exists():
        raise ConfigurationError(
            f"Configuration file not found: {env_file}\n"
            f"Available accounts: gre, upsc, test"
        )

    # Load environment variables
    load_dotenv(env_file)

    # Required fields
    required_fields = {
        'META_ADS_ACCOUNT_ID': os.getenv('META_ADS_ACCOUNT_ID'),
        'META_ACCESS_TOKEN': os.getenv('META_ACCESS_TOKEN'),
        'SLACK_WEBHOOK_URL': os.getenv('SLACK_WEBHOOK_URL'),
    }

    # Check for missing required fields
    missing_fields = [k for k, v in required_fields.items() if not v]
    if missing_fields:
        raise ConfigurationError(
            f"Missing required configuration in {env_file}:\n"
            f"  {', '.join(missing_fields)}\n"
            f"Please ensure all required fields are set."
        )

    # Build full config with defaults
    config = {
        'account_id': required_fields['META_ADS_ACCOUNT_ID'],
        'access_token': required_fields['META_ACCESS_TOKEN'],
        'slack_webhook': required_fields['SLACK_WEBHOOK_URL'],
        'account_name': os.getenv('ACCOUNT_NAME', account_name.upper()),
        'platforms': os.getenv('PLATFORMS'),
        'report_days': int(os.getenv('REPORT_DAYS', 7)),
        'timezone': os.getenv('TZ', 'Asia/Kolkata'),
        'db_path': os.getenv('DB_PATH', 'meta_ads_history.db'),
        'charts_dir': os.getenv('CHARTS_DIR', 'charts'),
        's3_bucket': os.getenv('S3_BUCKET', 'prepairo-analytics-reports'),
        'aws_region': os.getenv('AWS_REGION', 'ap-south-1'),
        'claude_model': os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929'),
        'report_interval_hours': int(os.getenv('REPORT_INTERVAL_HOURS', 8)),
    }

    return config
