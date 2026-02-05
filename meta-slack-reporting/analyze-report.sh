#!/bin/bash
# Simple wrapper for product team to run deep analysis

cd "$(dirname "$0")"
source venv/bin/activate

echo "Meta Ads Deep Analysis"
echo "======================"
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
echo "Options:"
echo "1) Full analysis (AI + Charts)"
echo "2) Without AI (faster)"
echo "3) Without charts (faster)"
echo "4) Quick (no AI, no charts)"
read -p "Enter choice (1-4, default: 1): " option_choice

AI="on"
CHARTS="on"

case $option_choice in
    2)
        AI="off"
        ;;
    3)
        CHARTS="off"
        ;;
    4)
        AI="off"
        CHARTS="off"
        ;;
esac

echo ""
echo "Running analysis for $ACCOUNT account..."
echo ""

python3 skills/meta-ads-analyze/tools/analyze_report.py \
    --account $ACCOUNT \
    --ai $AI \
    --charts $CHARTS
