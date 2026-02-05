#!/bin/bash
# Run Meta Ads Reporter for GRE account

cd "$(dirname "$0")"
source venv/bin/activate
cp .env.gre .env
python3 meta_ads_reporter_conversions.py
