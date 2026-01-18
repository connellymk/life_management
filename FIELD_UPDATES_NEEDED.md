# Airtable Field Updates Needed

## Summary

The health sync script expects specific field names in Airtable. You need to rename some fields in the **Training Sessions** table to match what the sync code expects.

## Status

- ✓ Health Metrics table: All fields are correct!
- ⚠️  Training Sessions table: 6 fields need to be renamed

## Required Changes

### Training Sessions Table

Rename these fields in Airtable UI:

| Current Field Name | New Field Name |
|-------------------|----------------|
| Duration (min) | Duration |
| Distance (mi) | Distance |
| Elevation Gain (ft) | Elevation Gain |
| Avg HR | Average HR |
| Avg Pace (min/mi) | Average Pace |
| Avg Speed (mph) | Average Speed |

## How to Rename Fields in Airtable

1. Open your Airtable base in a browser
2. Go to the **Training Sessions** table
3. For each field above:
   - Click the field header
   - Click "Customize field type"
   - Change the field name
   - Click "Save"

## Why These Changes?

The sync code was originally written to use clean field names without unit suffixes (e.g., "Duration" instead of "Duration (min)"). This keeps the code simpler and allows the units to be documented elsewhere (in field descriptions or documentation).

## After Renaming

Once you've renamed all 6 fields, run the health sync again:

```bash
python orchestrators/sync_health.py --start-date 2026-01-01 --end-date 2026-01-17
```

The sync should complete successfully without errors!

## Alternative: Update Sync Code Instead

If you prefer to keep your current field names in Airtable, you can update the sync code to use your existing field names. However, renaming the fields in Airtable is the recommended approach as it matches the original design.
