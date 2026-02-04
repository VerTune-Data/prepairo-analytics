#!/usr/bin/env python3
"""
Clicko Uptime Monitor
Checks https://clicko.prepairo.ai health and sends Slack alerts for issues
"""

import requests
import time
import socket
import ssl
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
import json

# Configuration from environment
CLICKO_URL = os.getenv('CLICKO_URL', 'https://clicko.prepairo.ai')
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_UPTIME')

if not SLACK_WEBHOOK:
    raise ValueError("SLACK_WEBHOOK_UPTIME environment variable not set")

# Thresholds
SLOW_RESPONSE_THRESHOLD = 1.0  # seconds
TIMEOUT = 10  # seconds

# Expected redirect domain
EXPECTED_REDIRECT_DOMAIN = "upsc.prepairo.ai"

# Expected app store IDs
ANDROID_APP_ID = "ai.prepairo.app"
IOS_APP_ID = "id6741750813"

# State file to track last alert time (avoid spam)
STATE_FILE = Path(__file__).parent / '.clicko_monitor_state.json'

# Logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'clicko_monitor_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_state():
    """Load last alert state"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_state(state):
    """Save alert state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def should_alert(alert_type, cooldown_minutes=0):
    """Check if enough time has passed since last alert of this type"""
    # CRITICAL SERVICE MODE: No cooldown - always alert
    # Every check sends an alert if there's an issue
    return True


def check_ssl_certificate(hostname):
    """Check SSL certificate validity"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

                # Check expiry
                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_until_expiry = (not_after - datetime.now()).days

                return {
                    'valid': True,
                    'days_until_expiry': days_until_expiry,
                    'expires_at': not_after.strftime('%Y-%m-%d %H:%M:%S')
                }
    except ssl.SSLError as e:
        return {
            'valid': False,
            'error': f"SSL Error: {str(e)}"
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f"Certificate check failed: {str(e)}"
        }


def check_platform_redirects():
    """Check Android and iOS redirects"""
    results = []

    # Android User-Agent
    android_ua = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
    # iOS User-Agent
    ios_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"

    for platform, user_agent in [("Android", android_ua), ("iOS", ios_ua)]:
        try:
            response = requests.get(
                CLICKO_URL,
                headers={'User-Agent': user_agent},
                timeout=TIMEOUT,
                allow_redirects=True,
                verify=True
            )

            final_url = response.url

            # Check if redirected to correct app store with correct app ID
            if platform == "Android":
                redirect_ok = ("play.google.com" in final_url and
                              f"id={ANDROID_APP_ID}" in final_url)
                if not redirect_ok:
                    if "play.google.com" in final_url:
                        logger.error(f"❌ Android redirect to WRONG APP → {final_url}")
                    else:
                        logger.error(f"❌ Android redirect to WRONG STORE → {final_url}")
            else:  # iOS
                # iOS can redirect to apps.apple.com or itms-apps:// protocol
                # Must contain the correct app ID
                is_app_store = ("apps.apple.com" in final_url or
                               final_url.startswith("itms-apps") or
                               final_url.startswith("itms://"))
                redirect_ok = is_app_store and IOS_APP_ID in final_url
                if not redirect_ok:
                    if is_app_store:
                        logger.error(f"❌ iOS redirect to WRONG APP → {final_url}")
                    else:
                        logger.error(f"❌ iOS redirect to WRONG STORE → {final_url}")

            results.append({
                'platform': platform,
                'final_url': final_url,
                'redirect_ok': redirect_ok,
                'status_code': response.status_code
            })

            if redirect_ok:
                logger.info(f"✅ {platform} redirect OK → PrepAiro app")
            else:
                logger.error(f"❌ {platform} redirect FAILED")

        except Exception as e:
            error_str = str(e)
            # iOS redirects to itms-apps protocol which requests library can't handle
            # This is actually a SUCCESS - it means the redirect is working
            # BUT we need to verify it's the correct app ID
            if platform == "iOS" and ("itms-apps" in error_str or "itms://" in error_str):
                # Check if the error message contains the correct iOS app ID
                if IOS_APP_ID in error_str:
                    logger.info(f"✅ {platform} redirect OK → PrepAiro iOS app (itms protocol)")
                    results.append({
                        'platform': platform,
                        'final_url': f'iOS App Store - PrepAiro ({IOS_APP_ID})',
                        'redirect_ok': True,
                        'status_code': 302  # Redirect success
                    })
                else:
                    logger.error(f"❌ {platform} redirect to WRONG APP (itms protocol) → {error_str}")
                    results.append({
                        'platform': platform,
                        'error': 'Redirected to wrong iOS app',
                        'redirect_ok': False
                    })
            else:
                logger.error(f"❌ {platform} check failed: {e}")
                results.append({
                    'platform': platform,
                    'error': str(e),
                    'redirect_ok': False
                })

    return results


def check_uptime():
    """Perform uptime check"""
    start_time = time.time()

    try:
        response = requests.get(
            CLICKO_URL,
            timeout=TIMEOUT,
            allow_redirects=True,
            verify=True
        )

        response_time = time.time() - start_time

        # Extract hostname for SSL check
        hostname = CLICKO_URL.replace('https://', '').replace('http://', '').split('/')[0]
        ssl_info = check_ssl_certificate(hostname)

        # Check final URL after redirects
        final_url = response.url
        final_domain = final_url.replace('https://', '').replace('http://', '').split('/')[0]
        redirect_ok = EXPECTED_REDIRECT_DOMAIN in final_domain

        # Determine status - only 2xx is truly "up"
        if 200 <= response.status_code < 300:
            if not redirect_ok:
                status = 'redirect_error'
                log_msg = f"❌ Clicko REDIRECT ERROR - Expected {EXPECTED_REDIRECT_DOMAIN}, got {final_domain}"
            else:
                status = 'up'
                log_msg = f"✅ Clicko UP - Status: {response.status_code}, Response: {round(response_time, 2)}s, Domain: {final_domain}"
        elif 400 <= response.status_code < 500:
            status = 'client_error'
            log_msg = f"❌ Clicko CLIENT ERROR - Status: {response.status_code}, Response: {round(response_time, 2)}s"
        else:
            status = 'server_error'
            log_msg = f"❌ Clicko SERVER ERROR - Status: {response.status_code}, Response: {round(response_time, 2)}s"

        result = {
            'status': status,
            'status_code': response.status_code,
            'response_time': round(response_time, 2),
            'is_slow': response_time > SLOW_RESPONSE_THRESHOLD,
            'ssl_valid': ssl_info.get('valid', False),
            'ssl_info': ssl_info,
            'final_url': final_url,
            'final_domain': final_domain,
            'redirect_ok': redirect_ok,
            'timestamp': datetime.now().isoformat(),
            'url': CLICKO_URL
        }

        logger.info(log_msg)

        return result

    except requests.exceptions.Timeout:
        logger.error(f"❌ Clicko TIMEOUT after {TIMEOUT}s")
        return {
            'status': 'timeout',
            'error': f'Request timeout after {TIMEOUT} seconds',
            'timestamp': datetime.now().isoformat(),
            'url': CLICKO_URL
        }

    except requests.exceptions.SSLError as e:
        logger.error(f"❌ Clicko SSL ERROR: {e}")
        return {
            'status': 'ssl_error',
            'error': f'SSL Certificate Error: {str(e)}',
            'timestamp': datetime.now().isoformat(),
            'url': CLICKO_URL
        }

    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Clicko DOWN - Connection Error: {e}")
        return {
            'status': 'down',
            'error': f'Connection Error: {str(e)}',
            'timestamp': datetime.now().isoformat(),
            'url': CLICKO_URL
        }

    except Exception as e:
        logger.error(f"❌ Clicko CHECK FAILED: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'url': CLICKO_URL
        }


def send_slack_alert(result):
    """Send alert to Slack"""
    status = result.get('status')

    # Determine alert type and message
    if status == 'down':
        if not should_alert('down', cooldown_minutes=15):
            logger.info("Skipping down alert (cooldown)")
            return

        color = "danger"
        title = "🔴 Clicko is DOWN!"
        message = f"*Error:* {result.get('error', 'Unknown error')}"

    elif status == 'timeout':
        if not should_alert('timeout', cooldown_minutes=15):
            logger.info("Skipping timeout alert (cooldown)")
            return

        color = "danger"
        title = f"⏱️ Clicko TIMEOUT ({TIMEOUT}s)"
        message = f"Server not responding within {TIMEOUT} seconds"

    elif status == 'ssl_error':
        if not should_alert('ssl_error', cooldown_minutes=60):
            logger.info("Skipping SSL alert (cooldown)")
            return

        color = "danger"
        title = "🔒 Clicko SSL Certificate Error"
        message = f"*Error:* {result.get('error', 'SSL validation failed')}"

    elif status == 'redirect_error':
        if not should_alert('redirect_error', cooldown_minutes=15):
            logger.info("Skipping redirect error alert (cooldown)")
            return

        color = "danger"
        title = "🔀 Clicko Redirect Error"
        message = f"*Expected:* {EXPECTED_REDIRECT_DOMAIN}\n*Got:* {result.get('final_domain', 'unknown')}"

    elif status == 'client_error':
        if not should_alert('client_error', cooldown_minutes=15):
            logger.info("Skipping client error alert (cooldown)")
            return

        color = "danger"
        title = f"❌ Clicko Client Error ({result['status_code']})"
        message = f"HTTP {result['status_code']} error - Page not found or invalid request"

    elif status == 'server_error' or result.get('status_code', 200) >= 500:
        if not should_alert('server_error', cooldown_minutes=15):
            logger.info("Skipping server error alert (cooldown)")
            return

        color = "danger"
        title = f"⚠️ Clicko Server Error ({result['status_code']})"
        message = f"HTTP {result['status_code']} error detected"

    elif result.get('is_slow'):
        if not should_alert('slow_response', cooldown_minutes=30):
            logger.info("Skipping slow response alert (cooldown)")
            return

        color = "warning"
        title = f"🐌 Clicko Slow Response"
        message = f"Response time: *{result['response_time']}s* (threshold: {SLOW_RESPONSE_THRESHOLD}s)"

    elif not result.get('ssl_valid') and result.get('ssl_info'):
        ssl_info = result['ssl_info']
        days = ssl_info.get('days_until_expiry')

        if days is not None and days < 30:
            if not should_alert('ssl_expiry', cooldown_minutes=1440):  # Once per day
                logger.info("Skipping SSL expiry alert (cooldown)")
                return

            color = "warning"
            title = f"🔒 Clicko SSL Certificate Expiring Soon"
            message = f"Certificate expires in *{days} days* ({ssl_info.get('expires_at')})"
        else:
            return  # Don't alert for other SSL issues if not critical
    else:
        # Everything is OK - no alert needed
        return

    # Build Slack message
    timestamp = datetime.fromisoformat(result['timestamp']).strftime('%Y-%m-%d %I:%M:%S %p IST')

    slack_message = {
        "attachments": [{
            "color": color,
            "title": title,
            "text": message,
            "fields": [
                {
                    "title": "URL",
                    "value": result['url'],
                    "short": True
                },
                {
                    "title": "Time",
                    "value": timestamp,
                    "short": True
                }
            ],
            "footer": "Clicko Uptime Monitor",
            "ts": int(time.time())
        }]
    }

    # Add additional fields based on status
    if result.get('response_time'):
        slack_message["attachments"][0]["fields"].append({
            "title": "Response Time",
            "value": f"{result['response_time']}s",
            "short": True
        })

    if result.get('status_code'):
        slack_message["attachments"][0]["fields"].append({
            "title": "Status Code",
            "value": str(result['status_code']),
            "short": True
        })

    try:
        response = requests.post(SLACK_WEBHOOK, json=slack_message)
        response.raise_for_status()
        logger.info(f"✅ Slack alert sent: {title}")
    except Exception as e:
        logger.error(f"❌ Failed to send Slack alert: {e}")


def send_platform_alert(result):
    """Send platform-specific redirect alert"""
    platform = result.get('platform')
    final_url = result.get('final_url', 'unknown')
    error = result.get('error')

    if error:
        title = f"📱 {platform} Redirect Check FAILED"
        message = f"*Error:* {error}"
    else:
        if platform == "Android":
            expected = f"play.google.com with app ID: {ANDROID_APP_ID}"
        else:
            expected = f"App Store with app ID: {IOS_APP_ID}"
        title = f"📱 {platform} Redirect Error"
        message = f"*Expected:* {expected}\n*Got:* {final_url}"

    timestamp = datetime.fromisoformat(result['timestamp']).strftime('%Y-%m-%d %I:%M:%S %p IST')

    slack_message = {
        "attachments": [{
            "color": "danger",
            "title": title,
            "text": message,
            "fields": [
                {
                    "title": "Platform",
                    "value": platform,
                    "short": True
                },
                {
                    "title": "Time",
                    "value": timestamp,
                    "short": True
                },
                {
                    "title": "Test URL",
                    "value": result['url'],
                    "short": False
                }
            ],
            "footer": "Clicko Platform Monitor",
            "ts": int(time.time())
        }]
    }

    try:
        response = requests.post(SLACK_WEBHOOK, json=slack_message)
        response.raise_for_status()
        logger.info(f"✅ Slack alert sent: {title}")
    except Exception as e:
        logger.error(f"❌ Failed to send Slack alert: {e}")


def main():
    """Main execution"""
    logger.info("🚀 Starting Clicko uptime check...")

    # Check main uptime
    result = check_uptime()
    send_slack_alert(result)

    # Check platform-specific redirects (Android/iOS)
    logger.info("🔍 Checking platform redirects...")
    platform_results = check_platform_redirects()

    # Alert if any platform redirect failed
    for platform_result in platform_results:
        if not platform_result.get('redirect_ok'):
            platform_alert = {
                'status': 'platform_redirect_error',
                'platform': platform_result['platform'],
                'final_url': platform_result.get('final_url', 'unknown'),
                'error': platform_result.get('error'),
                'timestamp': datetime.now().isoformat(),
                'url': CLICKO_URL
            }

            # Send platform redirect alert (no cooldown)
            send_platform_alert(platform_alert)

    logger.info("✅ Uptime check completed")


if __name__ == "__main__":
    main()
