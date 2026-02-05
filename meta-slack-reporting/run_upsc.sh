#!/bin/bash
# Run Meta Ads Reporter for UPSC account

cd "$(dirname "$0")"
source venv/bin/activate
cp .env.upsc .env
python3 meta_ads_reporter_conversions.py
