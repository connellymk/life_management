#!/usr/bin/env python3
"""Test script to check garth API structure"""

import garth
from garth import Activity, DailySteps, DailySleep, DailyStress, DailyHRV, WeightData
from datetime import date, timedelta
from core.config import GarminConfig as Config

# Authenticate
garth.login(Config.GARMIN_EMAIL, Config.GARMIN_PASSWORD)

# Test activities
print("=== Testing Activity ===")
activities = Activity.list(limit=1)
if activities:
    activity = activities[0]
    print(f"Activity attributes: {[a for a in dir(activity) if not a.startswith('_')]}")
    print(f"\nSample activity:")
    print(f"  start_time_local: {activity.start_time_local}")
    print(f"  duration: {activity.duration}")
    print(f"  distance: {activity.distance}")
    print(f"  calories: {activity.calories}")

# Test daily steps
print("\n=== Testing DailySteps ===")
today = date.today()
steps_list = DailySteps.list(end=today, period=1)
if steps_list:
    steps = steps_list[0]
    print(f"DailySteps attributes: {[a for a in dir(steps) if not a.startswith('_')]}")
    print(f"\nSample steps:")
    print(f"  calendar_date: {steps.calendar_date}")
    print(f"  total_steps: {steps.total_steps if hasattr(steps, 'total_steps') else 'N/A'}")
    print(f"  total_distance: {steps.total_distance if hasattr(steps, 'total_distance') else 'N/A'}")

# Test daily sleep
print("\n=== Testing DailySleep ===")
sleep_list = DailySleep.list(end=today, period=1)
if sleep_list:
    sleep = sleep_list[0]
    print(f"DailySleep attributes: {[a for a in dir(sleep) if not a.startswith('_')]}")

# Test weight
print("\n=== Testing WeightData ===")
weight_list = WeightData.list(end=today, days=1)
if weight_list:
    weight = weight_list[0]
    print(f"WeightData attributes: {[a for a in dir(weight) if not a.startswith('_')]}")
