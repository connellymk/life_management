#!/usr/bin/env python3
"""Check sample workouts from each type."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config

api = Api(Config.AIRTABLE_ACCESS_TOKEN)
table = api.table(Config.AIRTABLE_BASE_ID, "tblxSnGD6CS9ea0cM")
records = table.all()

# Get one sample of each type
samples = {}
for r in records:
    wtype = r["fields"].get("Workout Type")
    if wtype not in samples:
        samples[wtype] = r

print("=" * 70)
print("Sample Workouts by Type")
print("=" * 70)

for wtype in ["Cross Training", "Strength Training", "Rest Day", "Easy Run", "Long Run"]:
    if wtype in samples:
        r = samples[wtype]
        print(f"\n{wtype}:")
        print(f"  Name: {r['fields'].get('Name')}")
        print(f"  Duration: {r['fields'].get('Planned Duration', 'N/A')} min")
        desc = r['fields'].get('Workout Description', 'N/A')
        print(f"  Description: {desc[:80]}{'...' if len(desc) > 80 else ''}")
        print(f"  Pace/Effort: {r['fields'].get('Target Pace Effort', 'N/A')}")
        print(f"  Focus: {', '.join(r['fields'].get('Focus Areas', []))}")

print("\n" + "=" * 70)
print("Overall Completeness")
print("=" * 70)

with_description = len([r for r in records if r["fields"].get("Workout Description")])
with_pace = len([r for r in records if r["fields"].get("Target Pace Effort")])
with_focus = len([r for r in records if r["fields"].get("Focus Areas")])

print(f"\nTotal Workouts: {len(records)}")
print(f"  Workout Description: {with_description}/{len(records)} (100%)" if with_description == len(records) else f"  Workout Description: {with_description}/{len(records)}")
print(f"  Target Pace/Effort: {with_pace}/{len(records)} (100%)" if with_pace == len(records) else f"  Target Pace/Effort: {with_pace}/{len(records)}")
print(f"  Focus Areas: {with_focus}/{len(records)} (100%)" if with_focus == len(records) else f"  Focus Areas: {with_focus}/{len(records)}")

if with_description == with_pace == with_focus == len(records):
    print("\nALL WORKOUTS HAVE COMPLETE DETAILS!")
