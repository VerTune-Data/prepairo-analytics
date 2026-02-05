#!/bin/bash
# Test reports without sending to Slack (for testing only)

cd "$(dirname "$0")"
source venv/bin/activate

echo "Test Mode - Reports WITHOUT Slack Delivery"
echo "==========================================="
echo ""
echo "This will run reports but NOT send to Slack."
echo "Use this for testing only."
echo ""
echo "What do you want to test?"
echo "1) Quick report"
echo "2) Deep analysis (no AI, no charts)"
echo "3) Platform audit"
read -p "Enter choice (1-3): " test_choice

echo ""
echo "Which account?"
echo "1) GRE (default)"
echo "2) UPSC"
read -p "Enter choice (1-2): " account_choice

case $account_choice in
    2)
        ACCOUNT="upsc"
        ;;
    *)
        ACCOUNT="gre"
        ;;
esac

# Temporarily backup and remove Slack webhook to prevent sending
ENV_FILE=".env"
if [ "$ACCOUNT" != "gre" ]; then
    ENV_FILE=".env.$ACCOUNT"
fi

# Create backup
cp "$ENV_FILE" "${ENV_FILE}.backup"

# Remove Slack webhook temporarily
sed -i.tmp 's/^SLACK_WEBHOOK_URL=.*/SLACK_WEBHOOK_URL=https:\/\/hooks.slack.com\/test\/disabled/' "$ENV_FILE"

echo ""
echo "Running in TEST MODE (Slack disabled)..."
echo ""

case $test_choice in
    1)
        echo "Testing quick report..."
        python3 skills/meta-ads-quick/tools/quick_report.py --account $ACCOUNT --days 1 2>&1 | grep -v "Successfully sent"
        ;;
    2)
        echo "Testing deep analysis (no AI, no charts)..."
        python3 skills/meta-ads-analyze/tools/analyze_report.py --account $ACCOUNT --ai off --charts off 2>&1 | grep -v "Successfully sent"
        ;;
    3)
        echo "Testing platform audit..."
        python3 skills/meta-ads-audit/tools/audit_platforms.py --account $ACCOUNT
        ;;
esac

# Restore original config
mv "${ENV_FILE}.backup" "$ENV_FILE"
rm -f "${ENV_FILE}.tmp"

echo ""
echo "Test complete! Slack webhook restored."
