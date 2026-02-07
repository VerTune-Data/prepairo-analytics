#!/usr/bin/env python3
"""
Site Uptime Monitor
Checks PrepaIro sites for health, SSL, speed and sends Slack alerts for issues
Sends recovery alerts when sites come back up after downtime
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
from urllib.parse import urlparse

# Configuration from environment
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_SITE_ALERTS')

if not SLACK_WEBHOOK:
    raise ValueError("SLACK_WEBHOOK_SITE_ALERTS environment variable not set")

# Sites to monitor
SITES = [
    {
        'url': 'https://upsc.prepairo.ai',
        'name': 'UPSC PrepAiro',
        'expect_status': 200,
    },
    {
        'url': 'https://upsc.web.prepairo.ai',
        'name': 'UPSC Web PrepAiro',
        'expect_status': 200,
    },
    {
        'url': 'https://gre.prepairo.ai',
        'name': 'GRE PrepAiro',
        'expect_status': 200,
    },
    {
        'url': 'https://prepairo.ai',
        'name': 'PrepAiro Main',
        'expect_status': 200,
    },
    {
        'url': 'https://upsc.prepairo.ai/pricing',
        'name': 'UPSC Pricing Page',
        'expect_status': 200,
    },
]

# Thresholds
SLOW_RESPONSE_THRESHOLD = 3.0  # seconds
TIMEOUT = 15  # seconds
SSL_EXPIRY_WARNING_DAYS = 30
DNS_TIMEOUT = 5  # seconds

# State file to track site status across runs
STATE_FILE = Path(__file__).parent / '.site_monitor_state.json'

# Logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'site_monitor_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_state():
    """Load previous run state - tracks which sites had issues"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_state(state):
    """Save current run state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def check_dns(hostname):
    """Check DNS resolution"""
    try:
        start = time.time()
        ip_address = socket.gethostbyname(hostname)
        dns_time = time.time() - start
        return {
            'resolved': True,
            'ip_address': ip_address,
            'dns_time': round(dns_time, 3),
        }
    except socket.gaierror as e:
        return {
            'resolved': False,
            'error': f"DNS resolution failed: {str(e)}",
        }
    except socket.timeout:
        return {
            'resolved': False,
            'error': "DNS resolution timed out",
        }
    except Exception as e:
        return {
            'resolved': False,
            'error': f"DNS check failed: {str(e)}",
        }


def check_ssl_certificate(hostname):
    """Check SSL certificate validity and expiry"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

                # Check expiry
                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_until_expiry = (not_after - datetime.now()).days

                # Check issuer
                issuer = dict(x[0] for x in cert.get('issuer', []))
                issuer_name = issuer.get('organizationName', 'Unknown')

                # Check subject
                subject = dict(x[0] for x in cert.get('subject', []))
                common_name = subject.get('commonName', 'Unknown')

                # Check SANs
                san_list = []
                for san_type, san_value in cert.get('subjectAltName', []):
                    san_list.append(san_value)

                return {
                    'valid': True,
                    'days_until_expiry': days_until_expiry,
                    'expires_at': not_after.strftime('%Y-%m-%d %H:%M:%S'),
                    'issuer': issuer_name,
                    'common_name': common_name,
                    'san_count': len(san_list),
                    'expiring_soon': days_until_expiry < SSL_EXPIRY_WARNING_DAYS,
                }
    except ssl.SSLCertVerificationError as e:
        return {
            'valid': False,
            'error': f"SSL Verification Error: {str(e)}",
        }
    except ssl.SSLError as e:
        return {
            'valid': False,
            'error': f"SSL Error: {str(e)}",
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f"Certificate check failed: {str(e)}",
        }


def check_site(site):
    """Perform comprehensive health check on a single site"""
    url = site['url']
    name = site['name']
    expect_status = site.get('expect_status', 200)

    parsed = urlparse(url)
    hostname = parsed.hostname

    logger.info(f"🔍 Checking {name} ({url})...")

    issues = []
    result = {
        'url': url,
        'name': name,
        'timestamp': datetime.now().isoformat(),
        'checks': {},
    }

    # 1. DNS Check
    dns_result = check_dns(hostname)
    result['checks']['dns'] = dns_result
    if not dns_result['resolved']:
        logger.error(f"  ❌ DNS FAILED for {hostname}: {dns_result['error']}")
        issues.append({
            'type': 'dns_failure',
            'severity': 'critical',
            'title': f"🌐 DNS Resolution Failed - {name}",
            'message': dns_result['error'],
        })
        result['status'] = 'dns_failure'
        result['issues'] = issues
        return result
    else:
        logger.info(f"  ✅ DNS OK → {dns_result['ip_address']} ({dns_result['dns_time']}s)")

    # 2. SSL Certificate Check
    ssl_result = check_ssl_certificate(hostname)
    result['checks']['ssl'] = ssl_result
    if not ssl_result['valid']:
        logger.error(f"  ❌ SSL INVALID for {hostname}: {ssl_result['error']}")
        issues.append({
            'type': 'ssl_error',
            'severity': 'critical',
            'title': f"🔒 SSL Certificate Invalid - {name}",
            'message': ssl_result['error'],
        })
    elif ssl_result['expiring_soon']:
        days = ssl_result['days_until_expiry']
        logger.warning(f"  ⚠️ SSL expiring in {days} days for {hostname}")
        issues.append({
            'type': 'ssl_expiry',
            'severity': 'warning',
            'title': f"🔒 SSL Expiring Soon - {name}",
            'message': f"Certificate expires in *{days} days* ({ssl_result['expires_at']})\nIssuer: {ssl_result['issuer']}",
        })
    else:
        logger.info(f"  ✅ SSL OK - expires in {ssl_result['days_until_expiry']} days (Issuer: {ssl_result['issuer']})")

    # 3. HTTP Check (status code, response time, content)
    start_time = time.time()
    try:
        response = requests.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True,
            verify=True,
            headers={
                'User-Agent': 'PrepaIro-SiteMonitor/1.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
        )
        response_time = time.time() - start_time

        result['checks']['http'] = {
            'status_code': response.status_code,
            'response_time': round(response_time, 2),
            'content_length': len(response.content),
            'final_url': response.url,
            'redirect_count': len(response.history),
        }

        # Check status code
        if response.status_code != expect_status:
            if response.status_code >= 500:
                logger.error(f"  ❌ HTTP {response.status_code} SERVER ERROR ({response_time:.2f}s)")
                issues.append({
                    'type': 'server_error',
                    'severity': 'critical',
                    'title': f"⚠️ Server Error {response.status_code} - {name}",
                    'message': f"HTTP {response.status_code} error\nResponse time: {response_time:.2f}s",
                })
            elif response.status_code >= 400:
                logger.error(f"  ❌ HTTP {response.status_code} CLIENT ERROR ({response_time:.2f}s)")
                issues.append({
                    'type': 'client_error',
                    'severity': 'critical',
                    'title': f"❌ Client Error {response.status_code} - {name}",
                    'message': f"HTTP {response.status_code} error\nResponse time: {response_time:.2f}s",
                })
            elif response.status_code >= 300:
                logger.warning(f"  ⚠️ HTTP {response.status_code} REDIRECT ({response_time:.2f}s) → {response.url}")
                issues.append({
                    'type': 'unexpected_redirect',
                    'severity': 'warning',
                    'title': f"🔀 Unexpected Redirect - {name}",
                    'message': f"Expected {expect_status}, got {response.status_code}\nRedirected to: {response.url}",
                })
        else:
            logger.info(f"  ✅ HTTP {response.status_code} OK ({response_time:.2f}s)")

        # Check response time
        if response_time > SLOW_RESPONSE_THRESHOLD:
            logger.warning(f"  🐌 SLOW RESPONSE: {response_time:.2f}s (threshold: {SLOW_RESPONSE_THRESHOLD}s)")
            issues.append({
                'type': 'slow_response',
                'severity': 'warning',
                'title': f"🐌 Slow Response - {name}",
                'message': f"Response time: *{response_time:.2f}s* (threshold: {SLOW_RESPONSE_THRESHOLD}s)",
            })

        # Check content - basic validation that page returned HTML
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type and 'application/json' not in content_type:
            logger.warning(f"  ⚠️ Unexpected content type: {content_type}")
            issues.append({
                'type': 'content_type_error',
                'severity': 'warning',
                'title': f"📄 Unexpected Content Type - {name}",
                'message': f"Expected text/html, got: {content_type}",
            })

        # Check for empty response
        if len(response.content) < 100:
            logger.warning(f"  ⚠️ Suspiciously small response: {len(response.content)} bytes")
            issues.append({
                'type': 'empty_response',
                'severity': 'warning',
                'title': f"📄 Empty/Tiny Response - {name}",
                'message': f"Response body is only {len(response.content)} bytes",
            })

        result['status'] = 'up' if not issues else 'degraded'

    except requests.exceptions.Timeout:
        response_time = time.time() - start_time
        logger.error(f"  ❌ TIMEOUT after {TIMEOUT}s")
        result['checks']['http'] = {'error': f'Timeout after {TIMEOUT}s'}
        issues.append({
            'type': 'timeout',
            'severity': 'critical',
            'title': f"⏱️ Timeout ({TIMEOUT}s) - {name}",
            'message': f"Site did not respond within {TIMEOUT} seconds",
        })
        result['status'] = 'timeout'

    except requests.exceptions.SSLError as e:
        logger.error(f"  ❌ SSL ERROR during request: {e}")
        result['checks']['http'] = {'error': f'SSL Error: {str(e)}'}
        issues.append({
            'type': 'ssl_error',
            'severity': 'critical',
            'title': f"🔒 SSL Error During Request - {name}",
            'message': f"SSL error: {str(e)}",
        })
        result['status'] = 'ssl_error'

    except requests.exceptions.ConnectionError as e:
        logger.error(f"  ❌ CONNECTION ERROR: {e}")
        result['checks']['http'] = {'error': f'Connection Error: {str(e)}'}
        issues.append({
            'type': 'down',
            'severity': 'critical',
            'title': f"🔴 Site DOWN - {name}",
            'message': f"Connection failed: {str(e)}",
        })
        result['status'] = 'down'

    except Exception as e:
        logger.error(f"  ❌ CHECK FAILED: {e}")
        result['checks']['http'] = {'error': str(e)}
        issues.append({
            'type': 'error',
            'severity': 'critical',
            'title': f"💥 Check Failed - {name}",
            'message': f"Error: {str(e)}",
        })
        result['status'] = 'error'

    result['issues'] = issues
    return result


def send_slack_alert(issue, site_result):
    """Send a single issue alert to Slack"""
    severity = issue['severity']
    color = 'danger' if severity == 'critical' else 'warning'

    timestamp = datetime.fromisoformat(site_result['timestamp']).strftime('%Y-%m-%d %I:%M:%S %p IST')

    fields = [
        {
            'title': 'Site',
            'value': site_result['url'],
            'short': True,
        },
        {
            'title': 'Time',
            'value': timestamp,
            'short': True,
        },
    ]

    # Add HTTP details if available
    http_check = site_result.get('checks', {}).get('http', {})
    if http_check.get('response_time'):
        fields.append({
            'title': 'Response Time',
            'value': f"{http_check['response_time']}s",
            'short': True,
        })
    if http_check.get('status_code'):
        fields.append({
            'title': 'Status Code',
            'value': str(http_check['status_code']),
            'short': True,
        })

    # Add DNS info if available
    dns_check = site_result.get('checks', {}).get('dns', {})
    if dns_check.get('ip_address'):
        fields.append({
            'title': 'IP Address',
            'value': dns_check['ip_address'],
            'short': True,
        })

    slack_message = {
        'attachments': [{
            'color': color,
            'title': issue['title'],
            'text': issue['message'],
            'fields': fields,
            'footer': 'PrepaIro Site Monitor',
            'ts': int(time.time()),
        }]
    }

    try:
        response = requests.post(SLACK_WEBHOOK, json=slack_message)
        response.raise_for_status()
        logger.info(f"  ✅ Slack alert sent: {issue['title']}")
    except Exception as e:
        logger.error(f"  ❌ Failed to send Slack alert: {e}")


def send_recovery_alert(site_name, site_url, prev_issues, response_time=None):
    """Send a green recovery alert when a site comes back up"""
    # Build a summary of what was wrong
    issue_types = list(set(i['type'] for i in prev_issues))
    issue_summary = ', '.join(issue_types)
    down_since = prev_issues[0].get('first_seen', 'unknown')

    # Calculate downtime duration if we have first_seen
    duration_text = ""
    if down_since != 'unknown':
        try:
            first_seen_dt = datetime.fromisoformat(down_since)
            duration = datetime.now() - first_seen_dt
            minutes = int(duration.total_seconds() / 60)
            if minutes < 60:
                duration_text = f"\n*Downtime:* ~{minutes} minutes"
            else:
                hours = minutes // 60
                remaining_mins = minutes % 60
                duration_text = f"\n*Downtime:* ~{hours}h {remaining_mins}m"
        except:
            pass

    timestamp = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p IST')

    fields = [
        {
            'title': 'Site',
            'value': site_url,
            'short': True,
        },
        {
            'title': 'Time',
            'value': timestamp,
            'short': True,
        },
        {
            'title': 'Previous Issues',
            'value': issue_summary,
            'short': True,
        },
    ]

    if response_time is not None:
        fields.append({
            'title': 'Response Time',
            'value': f"{response_time}s",
            'short': True,
        })

    slack_message = {
        'attachments': [{
            'color': 'good',
            'title': f"✅ {site_name} is BACK UP!",
            'text': f"Site has recovered and is responding normally.{duration_text}",
            'fields': fields,
            'footer': 'PrepaIro Site Monitor',
            'ts': int(time.time()),
        }]
    }

    try:
        response = requests.post(SLACK_WEBHOOK, json=slack_message)
        response.raise_for_status()
        logger.info(f"  ✅ Recovery alert sent: {site_name} is back up!")
    except Exception as e:
        logger.error(f"  ❌ Failed to send recovery alert: {e}")


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("🚀 Starting PrepaIro site health checks...")
    logger.info("=" * 60)

    # Load previous state
    prev_state = load_state()
    new_state = {}

    all_results = []

    # Check all sites
    for site in SITES:
        result = check_site(site)
        all_results.append(result)

        site_key = result['url']
        has_issues = len(result.get('issues', [])) > 0
        was_down = site_key in prev_state and prev_state[site_key].get('has_issues', False)

        if has_issues:
            # Site has issues - send alerts and track state
            for issue in result['issues']:
                send_slack_alert(issue, result)

            # Preserve first_seen from previous state, or set it now
            first_seen = prev_state.get(site_key, {}).get('first_seen', datetime.now().isoformat())
            new_state[site_key] = {
                'has_issues': True,
                'first_seen': first_seen,
                'last_seen': datetime.now().isoformat(),
                'issues': [{'type': i['type'], 'first_seen': first_seen} for i in result['issues']],
            }
        else:
            # Site is healthy
            if was_down:
                # Was down before, now recovered — send recovery alert!
                prev_issues = prev_state[site_key].get('issues', [{'type': 'unknown'}])
                response_time = result.get('checks', {}).get('http', {}).get('response_time')
                send_recovery_alert(result['name'], result['url'], prev_issues, response_time)
                logger.info(f"  🎉 {result['name']} recovered from previous issues!")

            # Don't add to new_state — site is clean

        logger.info("")  # blank line between sites

    # Save new state
    save_state(new_state)

    # Summary
    healthy = sum(1 for r in all_results if not r['issues'])
    total = len(all_results)
    logger.info("=" * 60)
    logger.info(f"📊 Results: {healthy}/{total} sites healthy")

    for r in all_results:
        status_icon = "✅" if not r['issues'] else "❌"
        issue_count = len(r['issues'])
        extra = f" ({issue_count} issue{'s' if issue_count != 1 else ''})" if r['issues'] else ""
        logger.info(f"  {status_icon} {r['name']}: {r.get('status', 'unknown')}{extra}")

    logger.info("=" * 60)
    logger.info("✅ Site health checks completed")


if __name__ == "__main__":
    main()
