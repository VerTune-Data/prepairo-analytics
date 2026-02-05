#!/bin/bash
# Simple wrapper for product team to run quick reports

cd "$(dirname "$0")"
source venv/bin/activate

echo "Meta Ads Quick Report"
echo "====================="
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

read -p "How many days? (default: 7): " days
DAYS=${days:-7}

echo ""
echo "Running report for $ACCOUNT account (last $DAYS days)..."
echo ""

python3 skills/meta-ads-quick/tools/quick_report.py --account $ACCOUNT --days $DAYS
