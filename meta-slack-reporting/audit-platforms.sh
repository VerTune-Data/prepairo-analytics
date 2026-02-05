#!/bin/bash
# Simple wrapper for product team to audit platform configuration

cd "$(dirname "$0")"
source venv/bin/activate

echo "Meta Ads Platform Audit"
echo "======================="
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

echo ""
echo "Auditing $ACCOUNT account..."
echo ""

python3 skills/meta-ads-audit/tools/audit_platforms.py --account $ACCOUNT
