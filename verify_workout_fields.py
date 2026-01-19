#!/usr/bin/env python3
"""Verify Workout Type and Workout Detail fields are populated correctly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config

api = Api(Config.AIRTABLE_ACCESS_TOKEN)
table = api.table(Config.AIRTABLE_BASE_ID, "tblxSnGD6CS9ea0cM")
records = table.all()

# Get one sample of each workout detail
samples = {}
for r in records:
    detail = r["fields"].get("Workout Detail")
    if detail and detail not in samples:
        samples[detail] = r

print("=" * 70)
print("Sample Workouts - Workout Type vs Workout Detail")
print("=" * 70)

for detail in ["Long Run", "Easy Run", "Hill Workout", "Cross Training", "Strength Training", "Rest Day"]:
    if detail in samples:
        r = samples[detail]
        print(f"\n{detail}:")
        print(f"  Workout Type (Base Activity): {r['fields'].get('Workout Type')}")
        print(f"  Workout Detail (Specific): {r['fields'].get('Workout Detail')}")
        print(f"  Name: {r['fields'].get('Name')}")

print("\n" + "=" * 70)
print("Field Completeness Check")
print("=" * 70)

with_type = len([r for r in records if r["fields"].get("Workout Type")])
with_detail = len([r for r in records if r["fields"].get("Workout Detail")])

print(f"\nTotal Workouts: {len(records)}")
print(f"  With Workout Type: {with_type}/{len(records)} (100%)" if with_type == len(records) else f"  With Workout Type: {with_type}/{len(records)}")
print(f"  With Workout Detail: {with_detail}/{len(records)} (100%)" if with_detail == len(records) else f"  With Workout Detail: {with_detail}/{len(records)}")

if with_type == with_detail == len(records):
    print("\nBoth fields are 100% populated!")
