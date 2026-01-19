#!/usr/bin/env python3
"""Verify training plan completeness."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config

api = Api(Config.AIRTABLE_ACCESS_TOKEN)
table = api.table(Config.AIRTABLE_BASE_ID, "tblxSnGD6CS9ea0cM")
records = table.all()

# Get all running workouts
running_workouts = [r for r in records if "Run" in r["fields"].get("Workout Type", "")]

# Calculate totals
total_miles = sum([r["fields"].get("Planned Distance", 0) for r in running_workouts])
total_elevation = sum([r["fields"].get("Planned Elevation Gain", 0) for r in running_workouts])

# Breakdown by type
by_type = {}
for r in running_workouts:
    wtype = r["fields"].get("Workout Type")
    if wtype not in by_type:
        by_type[wtype] = {"count": 0, "miles": 0, "elevation": 0}
    by_type[wtype]["count"] += 1
    by_type[wtype]["miles"] += r["fields"].get("Planned Distance", 0)
    by_type[wtype]["elevation"] += r["fields"].get("Planned Elevation Gain", 0)

print("=" * 60)
print("Training Plan Running Summary")
print("=" * 60)
print(f"\nTotal Running Miles: {total_miles:.1f} miles")
print(f"Total Elevation Gain: {total_elevation:,} feet")
print(f"\nBreakdown by Workout Type:\n")

for wtype, data in sorted(by_type.items()):
    print(f"{wtype}:")
    print(f"  Count: {data['count']}")
    print(f"  Miles: {data['miles']:.1f}")
    print(f"  Elevation: {data['elevation']:,} ft")
    print()

# Check completeness
print("=" * 60)
print("Data Completeness Check")
print("=" * 60)

with_distance = len([r for r in running_workouts if r["fields"].get("Planned Distance")])
with_elevation = len([r for r in running_workouts if r["fields"].get("Planned Elevation Gain")])
with_description = len([r for r in running_workouts if r["fields"].get("Workout Description")])
with_pace = len([r for r in running_workouts if r["fields"].get("Target Pace Effort")])

print(f"\nTotal running workouts: {len(running_workouts)}")
print(f"  With Planned Distance: {with_distance} (100%)" if with_distance == len(running_workouts) else f"  With Planned Distance: {with_distance} ({with_distance/len(running_workouts)*100:.0f}%)")
print(f"  With Planned Elevation: {with_elevation} (100%)" if with_elevation == len(running_workouts) else f"  With Planned Elevation: {with_elevation} ({with_elevation/len(running_workouts)*100:.0f}%)")
print(f"  With Workout Description: {with_description} (100%)" if with_description == len(running_workouts) else f"  With Workout Description: {with_description} ({with_description/len(running_workouts)*100:.0f}%)")
print(f"  With Target Pace/Effort: {with_pace} (100%)" if with_pace == len(running_workouts) else f"  With Target Pace/Effort: {with_pace} ({with_pace/len(running_workouts)*100:.0f}%)")

if with_distance == with_elevation == with_description == with_pace == len(running_workouts):
    print("\n✓ ALL RUNNING WORKOUTS HAVE COMPLETE DETAILS!")
else:
    print("\n⚠ Some workouts are missing details")
