"""
Verify that all core tables have the expected fields.
"""

import requests
from core.config import AirtableConfig

def main():
    access_token = AirtableConfig.AIRTABLE_ACCESS_TOKEN or AirtableConfig.AIRTABLE_API_KEY
    base_id = AirtableConfig.AIRTABLE_BASE_ID
    base_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return

    tables = {t["name"]: t for t in response.json()["tables"]}

    # Expected fields for each table
    expected_fields = {
        "Calendar Events": [
            "Event ID", "Title", "Day", "Date", "Start Time", "End Time",
            "Duration (min)", "All Day", "Calendar", "Location", "Description",
            "Attendees", "Status", "Recurring", "Last Synced"
        ],
        "Training Sessions": [
            "Activity ID", "Activity Name", "Day", "Week", "Date", "Start Time",
            "Activity Type", "Duration (min)", "Distance (mi)", "Elevation Gain (ft)",
            "Avg HR", "Max HR", "Avg Pace (min/mi)", "Calories", "Training Effect",
            "Notes", "Source", "Last Synced"
        ],
        "Health Metrics": [
            "Day", "Date", "Resting HR", "HRV", "Steps", "Floors Climbed",
            "Active Calories", "Total Calories", "Sleep Duration (hr)", "Sleep Score",
            "Deep Sleep (min)", "REM Sleep (min)", "Light Sleep (min)", "Stress Level",
            "Body Battery", "VO2 Max", "Hydration (oz)", "Last Synced"
        ],
        "Body Metrics": [
            "Measurement ID", "Day", "Date", "Weight (lbs)", "Body Fat %",
            "Muscle Mass (lbs)", "BMI", "Bone Mass (lbs)", "Water %",
            "Source", "Notes", "Last Synced"
        ],
        "Training Plans": [
            "Plan Name", "Race/Event", "Event Date", "Start Week", "End Week",
            "Total Weeks", "Current Phase", "Weekly Mileage Target", "Key Workouts",
            "Priority", "Status", "Notes"
        ]
    }

    print("=" * 70)
    print("TABLE SCHEMA VERIFICATION")
    print("=" * 70)
    print()

    all_complete = True

    for table_name, expected in expected_fields.items():
        if table_name not in tables:
            print(f"✗ {table_name}: TABLE NOT FOUND")
            all_complete = False
            continue

        table = tables[table_name]
        actual_fields = [f["name"] for f in table.get("fields", [])]

        missing = set(expected) - set(actual_fields)
        extra = set(actual_fields) - set(expected)

        if not missing:
            print(f"✓ {table_name}: All {len(expected)} expected fields present")
        else:
            print(f"⚠ {table_name}: {len(missing)} field(s) missing")
            for field in missing:
                print(f"    - Missing: {field}")
            all_complete = False

        if extra:
            print(f"    + Extra fields: {', '.join(extra)}")

        print()

    print("=" * 70)
    if all_complete:
        print("✓ ALL TABLES COMPLETE AND READY FOR SYNC")
    else:
        print("⚠ SOME TABLES NEED ATTENTION")
    print("=" * 70)


if __name__ == "__main__":
    main()
