# Meta Ads Audit

Check which platforms (Facebook vs Instagram) are configured for your campaigns and adsets.

## What This Does

Inspects the platform configuration for all campaigns and adsets to identify which ads run on Facebook, Instagram, or both. Highlights misconfigurations where active adsets have Facebook enabled despite Instagram-only policies.

## Usage

```bash
/meta-ads-audit [--account gre|upsc]
```

## Arguments

- `--account` (optional): Account to audit
  - `gre` (default): PrepAiro GRE account
  - `upsc`: UPSC account

## What You Get

1. **Campaign Hierarchy**: Full breakdown of all campaigns and their adsets
2. **Platform Configuration**: Shows which platforms each adset is configured to run on:
   - `publisher_platforms`: Explicit platform targeting (facebook, instagram, etc.)
   - Empty/Automatic: Runs on all platforms (Facebook + Instagram + more)
3. **Status Indicators**: Shows if each campaign/adset is ACTIVE, PAUSED, etc.
4. **Configuration Alerts**: Highlights active adsets with Facebook enabled:
   - 🔴 **FACEBOOK IS ENABLED AND ACTIVE** - Immediate action needed
   - ⚠️  Facebook is configured but adset is paused

## Output

Terminal report showing:
- All campaigns with their status
- All adsets under each campaign
- Platform configuration for each adset
- Warnings for Facebook-enabled active adsets
- Summary with actionable recommendations

## Use Cases

- **Verify Instagram-Only Configuration**: Ensure campaigns only run on Instagram
- **Audit Platform Spend**: Identify where budget is being allocated
- **Troubleshoot Reporting**: Understand why certain ads appear in reports
- **Configuration Validation**: Check if Meta Ads Manager settings match expectations

## Examples

```bash
# Audit GRE account
/meta-ads-audit

# Audit UPSC account
/meta-ads-audit --account upsc
```

## Sample Output

```
================================================================================
Checking Platform Configuration for All Campaigns & AdSets
================================================================================

📊 Campaign: UPSC Instagram Campaign
   ID: 123456789
   Status: ACTIVE
   └─ AdSet: Test AdSet 1
      Status: ACTIVE
      Publisher Platforms: instagram
      Instagram Positions: stream, story, explore

   └─ AdSet: Test AdSet 2
      Status: ACTIVE
      Publisher Platforms: Automatic Placements (all platforms)
      🔴 FACEBOOK IS ENABLED AND ACTIVE ON THIS ADSET!

================================================================================
Summary:
If you see 'FACEBOOK IS ENABLED' warnings above, those adsets are still
configured to run on Facebook. You need to edit them in Meta Ads Manager.
================================================================================
```

## Requirements

- Meta Ads account configured in `.env` file
- Valid Meta access token

## Notes

- Shows all campaigns regardless of status (active, paused, archived)
- Empty `publisher_platforms` means Automatic Placements (all platforms including Facebook)
- Platform changes in Meta Ads Manager can take 15-30 minutes to propagate
- Individual ads may have placement overrides independent of parent adset
