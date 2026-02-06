#!/bin/bash
# Setup script for competitor ads scraper on EC2
# Run this once to install dependencies

set -e

echo "=== Setting up Competitor Ads Scraper ==="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install Playwright Python package
echo "Installing Playwright..."
pip install playwright

# Install Chromium browser (headless)
echo "Installing Chromium browser..."
playwright install chromium

# Install system dependencies for Chromium (Ubuntu/Debian)
echo "Installing system dependencies..."
sudo apt-get update -y || true
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    2>/dev/null || echo "Some dependencies may already be installed"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Usage:"
echo "  python competitor_ads_scraper.py --competitor superkalam"
echo "  python competitor_ads_scraper.py --competitor all"
echo "  python competitor_ads_scraper.py --page-id 102666082828113 --name 'SuperKalam'"
echo ""
echo "Available competitors: superkalam, csewhy, prepairo, visionias, drishtiias"
