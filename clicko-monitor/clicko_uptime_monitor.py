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
SLOW_RESPONSE_THRESHOLD = 3.0  # seconds
TIMEOUT = 10  # seconds

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


def should_alert(alert_type, cooldown_minutes=15):
    """Check if enough time has passed since last alert of this type"""
    state = load_state()
    last_alert_key = f"last_{alert_type}_alert"

    if last_alert_key in state:
        last_alert = datetime.fromisoformat(state[last_alert_key])
        if datetime.now() - last_alert < timedelta(minutes=cooldown_minutes):
            return False

    # Update state
    state[last_alert_key] = datetime.now().isoformat()
    save_state(state)
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

        result = {
            'status': 'up' if response.status_code < 500 else 'error',
            'status_code': response.status_code,
            'response_time': round(response_time, 2),
            'is_slow': response_time > SLOW_RESPONSE_THRESHOLD,
            'ssl_valid': ssl_info.get('valid', False),
            'ssl_info': ssl_info,
            'timestamp': datetime.now().isoformat(),
            'url': CLICKO_URL
        }

        logger.info(f"✅ Clicko UP - Status: {result['status_code']}, "
                   f"Response: {result['response_time']}s")

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

    elif result.get('status_code', 200) >= 500:
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


def main():
    """Main execution"""
    logger.info("🚀 Starting Clicko uptime check...")

    result = check_uptime()

    # Send alert if there's an issue
    send_slack_alert(result)

    logger.info("✅ Uptime check completed")


if __name__ == "__main__":
    main()
