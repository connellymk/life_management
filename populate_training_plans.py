#!/usr/bin/env python3
"""
Populate Training Plans table based on Beaverhead 100k Training Plan.
Creates 175 workouts across 25 weeks (Jan 20 - Jul 12, 2026).
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("populate_training_plans")

TRAINING_PLANS_TABLE_ID = "tblxSnGD6CS9ea0cM"
WEEK_TABLE_ID = "tbl2B7ecl7heYiKha"
DAY_TABLE_ID = "tblHMwUnVg8bA1xoP"

# Race date
RACE_DATE = datetime(2026, 7, 12)  # Saturday, July 12, 2026
TRAINING_START = datetime(2026, 1, 19)  # Week 1 starts Monday, Jan 19, 2026


# Training plan structure by phase and week
TRAINING_PLAN = {
    # Phase 1: Base Building (Weeks 1-8)
    "Base Building": {
        "weeks": range(1, 9),
        "weekly_structure": {
            "Monday": {"type": "Rest Day", "priority": "Important"},
            "Tuesday": {"type": "Cross Training", "priority": "Standard", "duration": 60},
            "Wednesday": {"type": "Easy Run", "priority": "Standard"},
            "Thursday": {"type": "Cross Training", "priority": "Optional", "duration": 60},
            "Friday": {"type": "Rest Day", "priority": "Important", "description": "Yoga/Mobility (45-50 min)"},
            "Saturday": {"type": "Long Run", "priority": "Key Workout"},
            "Sunday": {"type": "Cross Training", "priority": "Standard", "duration": 90},
        },
        "weekly_mileage": {
            1: 20, 2: 25, 3: 28, 4: 22, 5: 30, 6: 32, 7: 35, 8: 25
        },
        "saturday_long_runs": {
            1: {"distance": 8, "elevation": 800, "description": "Easy rolling terrain"},
            2: {"distance": 10, "elevation": 1000, "description": "Easy hills"},
            3: {"distance": 12, "elevation": 1200, "description": "Moderate hills"},
            4: {"distance": 8, "elevation": 800, "description": "Recovery week - easy terrain"},
            5: {"distance": 13, "elevation": 1400, "description": "Progressive terrain"},
            6: {"distance": 14, "elevation": 1500, "description": "Sustained climbing"},
            7: {"distance": 16, "elevation": 1800, "description": "Building vertical"},
            8: {"distance": 10, "elevation": 1000, "description": "Recovery week"},
        }
    },

    # Phase 2: Build 1 (Weeks 9-14)
    "Build 1": {
        "weeks": range(9, 15),
        "weekly_structure": {
            "Monday": {"type": "Strength Training", "priority": "Important", "duration": 60},
            "Tuesday": {"type": "Easy Run", "priority": "Standard"},
            "Wednesday": {"type": "Hill Workout", "priority": "Key Workout"},
            "Thursday": {"type": "Recovery Run", "priority": "Optional"},
            "Friday": {"type": "Rest Day", "priority": "Important", "description": "Yoga/Mobility (45-50 min)"},
            "Saturday": {"type": "Long Run", "priority": "Key Workout"},
            "Sunday": {"type": "Cross Training", "priority": "Standard", "duration": 90},
        },
        "weekly_mileage": {
            9: 35, 10: 40, 11: 42, 12: 32, 13: 45, 14: 42
        },
        "saturday_long_runs": {
            9: {"distance": 16, "elevation": 1800, "description": "Steady climbing"},
            10: {"distance": 18, "elevation": 2200, "description": "Back-to-back weekend - Day 1"},
            11: {"distance": 18, "elevation": 2000, "description": "Sustained effort"},
            12: {"distance": 14, "elevation": 1400, "description": "Recovery week"},
            13: {"distance": 20, "elevation": 2500, "description": "First 20-miler! Back-to-back weekend - Day 1"},
            14: {"distance": 18, "elevation": 2000, "description": "Building confidence"},
        },
        "wednesday_workouts": {
            9: {"description": "Hill repeats: 5x 3min sustained climbs, easy recovery jogs", "elevation": 800},
            10: {"description": "Hill repeats: 6x 3min sustained climbs, easy recovery", "elevation": 900},
            11: {"description": "Hill repeats: 5x 4min sustained climbs, focus on form", "elevation": 1000},
            12: {"description": "Easy hills: 30min continuous rolling terrain", "elevation": 500},
            13: {"description": "Hill repeats: 6x 4min sustained climbs, strong effort", "elevation": 1200},
            14: {"description": "Hill repeats: 5x 5min sustained climbs, tempo effort", "elevation": 1200},
        },
        "sunday_runs": {
            10: {"type": "Easy Run", "distance": 10, "elevation": 800, "description": "Back-to-back Day 2 - easy effort"},
            13: {"type": "Easy Run", "distance": 12, "elevation": 1000, "description": "Back-to-back Day 2 - steady effort"},
        }
    },

    # Phase 3: Build 2 (Weeks 15-20)
    "Build 2": {
        "weeks": range(15, 21),
        "weekly_structure": {
            "Monday": {"type": "Strength Training", "priority": "Important", "duration": 60},
            "Tuesday": {"type": "Easy Run", "priority": "Standard"},
            "Wednesday": {"type": "Hill Workout", "priority": "Key Workout"},  # Alternates with tempo
            "Thursday": {"type": "Recovery Run", "priority": "Optional"},
            "Friday": {"type": "Rest Day", "priority": "Important", "description": "Yoga/Mobility (45-50 min)"},
            "Saturday": {"type": "Long Run", "priority": "Key Workout"},
            "Sunday": {"type": "Cross Training", "priority": "Standard", "duration": 90},
        },
        "weekly_mileage": {
            15: 45, 16: 50, 17: 48, 18: 42, 19: 55, 20: 50
        },
        "saturday_long_runs": {
            15: {"distance": 22, "elevation": 3000, "description": "Building to peak mileage"},
            16: {"distance": 24, "elevation": 3500, "description": "Back-to-back weekend - Day 1"},
            17: {"distance": 26, "elevation": 3800, "description": "Progressive long run"},
            18: {"distance": 20, "elevation": 2500, "description": "Recovery week - maintain fitness"},
            19: {"distance": 30, "elevation": 4500, "description": "PEAK WEEK! Back-to-back - Day 1"},
            20: {"distance": 32, "elevation": 4800, "description": "LONGEST RUN! Full race simulation"},
        },
        "wednesday_workouts": {
            15: {"type": "Tempo Run", "description": "8 miles tempo: 15min warmup, 40min comfortably hard (9:00-9:30/mi), 10min cooldown", "elevation": 400},
            16: {"type": "Hill Workout", "description": "Hill repeats: 6x 5min sustained climbs, strong effort", "elevation": 1500},
            17: {"type": "Tempo Run", "description": "10 miles tempo: 15min warmup, 50min comfortably hard, 10min cooldown", "elevation": 500},
            18: {"type": "Hill Workout", "description": "Easy hills: 40min continuous moderate terrain", "elevation": 800},
            19: {"type": "Tempo Run", "description": "12 miles tempo: 20min warmup, 60min comfortably hard, 15min cooldown", "elevation": 600},
            20: {"type": "Hill Workout", "description": "Hill repeats: 8x 4min sustained climbs, race-effort", "elevation": 1400},
        },
        "sunday_runs": {
            16: {"type": "Easy Run", "distance": 13, "elevation": 1200, "description": "Back-to-back Day 2 - steady recovery"},
            19: {"type": "Easy Run", "distance": 14, "elevation": 1400, "description": "Back-to-back Day 2 - managing fatigue"},
        }
    },

    # Phase 4: Peak (Weeks 21-22)
    "Peak": {
        "weeks": range(21, 23),
        "weekly_structure": {
            "Monday": {"type": "Strength Training", "priority": "Important", "duration": 60},
            "Tuesday": {"type": "Easy Run", "priority": "Standard"},
            "Wednesday": {"type": "Hill Workout", "priority": "Key Workout"},
            "Thursday": {"type": "Recovery Run", "priority": "Optional"},
            "Friday": {"type": "Rest Day", "priority": "Important", "description": "Yoga/Mobility (45-50 min)"},
            "Saturday": {"type": "Long Run", "priority": "Key Workout"},
            "Sunday": {"type": "Cross Training", "priority": "Standard", "duration": 90},
        },
        "weekly_mileage": {
            21: 50, 22: 45
        },
        "saturday_long_runs": {
            21: {"distance": 31, "elevation": 4500, "description": "50K RACE SIMULATION! 4:00 AM start, full gear and nutrition"},
            22: {"distance": 25, "elevation": 3500, "description": "Final confidence builder"},
        },
        "wednesday_workouts": {
            21: {"description": "Hill repeats: 6x 5min sustained climbs, race-specific effort", "elevation": 1500},
            22: {"description": "Hill repeats: 5x 4min sustained climbs, controlled effort", "elevation": 1200},
        }
    },

    # Phase 5: Taper (Weeks 23-25)
    "Taper": {
        "weeks": range(23, 26),
        "weekly_structure": {
            "Monday": {"type": "Rest Day", "priority": "Important"},
            "Tuesday": {"type": "Easy Run", "priority": "Standard"},
            "Wednesday": {"type": "Easy Run", "priority": "Standard", "description": "Include strides"},
            "Thursday": {"type": "Recovery Run", "priority": "Optional"},
            "Friday": {"type": "Rest Day", "priority": "Important", "description": "Yoga/Mobility (30 min)"},
            "Saturday": {"type": "Long Run", "priority": "Key Workout"},
            "Sunday": {"type": "Cross Training", "priority": "Optional", "duration": 60},
        },
        "weekly_mileage": {
            23: 28, 24: 20, 25: 8  # Week 25 is race week
        },
        "saturday_long_runs": {
            23: {"distance": 15, "elevation": 1500, "description": "Taper begins - comfortable effort"},
            24: {"distance": 10, "elevation": 1000, "description": "Final long run - feeling fresh"},
            25: {"distance": 62.1, "elevation": 12700, "description": "RACE DAY! Beaverhead 100k 🏔️"},
        },
        "wednesday_workouts": {
            23: {"description": "6 miles easy with 6x 20sec strides", "elevation": 200},
            24: {"description": "4 miles easy with 4x 20sec strides", "elevation": 150},
            25: {"description": "2 miles shakeout with 3x 10sec pickups", "elevation": 100},
        }
    }
}


def get_week_phase(week_num):
    """Get training phase for a given week number."""
    for phase, data in TRAINING_PLAN.items():
        if week_num in data["weeks"]:
            return phase
    return None


def calculate_non_long_run_distances(week_num, phase, total_weekly_mileage, long_run_distance):
    """Calculate distances for other runs in the week."""
    remaining_mileage = total_weekly_mileage - long_run_distance

    # Distribution depends on phase
    if phase == "Base Building":
        # Tuesday: 20%, Wednesday: 25%, Thursday: 15%, Sunday: 40%
        return {
            "Tuesday": round(remaining_mileage * 0.20, 1),
            "Wednesday": round(remaining_mileage * 0.25, 1),
            "Thursday": round(remaining_mileage * 0.15, 1),
            "Sunday": round(remaining_mileage * 0.40, 1),
        }
    else:
        # Tuesday: 20%, Wednesday: 30%, Thursday: 15%, Sunday: 35%
        return {
            "Tuesday": round(remaining_mileage * 0.20, 1),
            "Wednesday": round(remaining_mileage * 0.30, 1),
            "Thursday": round(remaining_mileage * 0.15, 1),
            "Sunday": round(remaining_mileage * 0.35, 1),
        }


def get_base_activity_type(workout_detail):
    """Map workout detail to base activity type."""
    running_types = ["Long Run", "Easy Run", "Tempo Run", "Hill Workout", "Intervals", "Recovery Run"]

    if workout_detail in running_types:
        return "Running"
    elif workout_detail == "Strength Training":
        return "Strength-Training"
    elif workout_detail == "Cross Training":
        # Could be multiple - we'll use a generic "Cross-Training" type
        # Or could be more specific based on season/phase
        return "Cross-Training"
    elif workout_detail == "Rest Day":
        return "Rest"
    else:
        return "Other"


def create_workout_record(week_num, day_record_id, weekday, workout_data, phase):
    """Create a single workout record."""
    workout_detail = workout_data["type"]
    priority = workout_data.get("priority", "Standard")

    # Get base activity type
    base_activity = get_base_activity_type(workout_detail)

    # Base record
    record = {
        "Day": [day_record_id],
        "Workout Type": base_activity,
        "Workout Detail": workout_detail,
        "Training Phase": phase,
        "Priority": priority,
        "Status": "Planned",
    }

    # Add name
    if workout_detail == "Rest Day":
        if "Yoga" in workout_data.get("description", ""):
            record["Name"] = f"Week {week_num} - {weekday}: Yoga/Mobility"
        else:
            record["Name"] = f"Week {week_num} - {weekday}: Rest"
    else:
        record["Name"] = f"Week {week_num} - {weekday}: {workout_detail}"

    # Add workout-specific fields
    if "distance" in workout_data:
        record["Planned Distance"] = workout_data["distance"]

    if "duration" in workout_data:
        record["Planned Duration"] = workout_data["duration"]

    if "elevation" in workout_data:
        record["Planned Elevation Gain"] = workout_data["elevation"]

    # Add or enhance descriptions for all workout types
    if "description" in workout_data:
        record["Workout Description"] = workout_data["description"]
    else:
        # Add default descriptions for workouts without custom descriptions
        if workout_detail == "Cross Training":
            if week_num <= 8:
                # Base building phase - emphasize nordic skiing
                record["Workout Description"] = "Nordic skiing (classic or skate), bike trainer, or indoor climbing. Focus on aerobic base building. Maintain conversational effort."
            else:
                # Build phases - more varied
                record["Workout Description"] = "Choose: Nordic skiing, cycling, swimming, or climbing. Maintain steady aerobic effort. Support running durability."
        elif workout_detail == "Strength Training":
            if week_num <= 14:
                # Early build phase
                record["Workout Description"] = "Full body strength: Focus on legs (squats, lunges, step-ups), core stability, and upper body. 3 sets x 10-12 reps. Include balance work."
            elif week_num <= 20:
                # Peak build phase
                record["Workout Description"] = "Maintenance strength: Focus on single-leg exercises, core endurance, and injury prevention. 2-3 sets x 8-10 reps. Keep intensity moderate."
            else:
                # Peak/taper
                record["Workout Description"] = "Light maintenance: Body weight exercises, core work, mobility drills. Focus on maintaining strength without adding fatigue."
        elif workout_detail == "Rest Day":
            if "Yoga" in record["Name"]:
                if weekday == "Friday":
                    record["Workout Description"] = "Yoga and mobility work: Hip openers, hamstring stretches, thoracic mobility, ankle mobility. Foam rolling for recovery. 45-50 minutes."
                else:
                    record["Workout Description"] = "Active recovery: Gentle stretching, foam rolling, mobility work. Focus on areas of tightness. 30-45 minutes."
            else:
                # Plain rest days (usually Monday in base building and taper)
                record["Workout Description"] = "Complete rest day. Focus on sleep, nutrition, and mental recovery. Light walking is okay if needed."

    # Add focus areas - ALWAYS populate this field
    focus_areas = []
    if workout_detail == "Long Run":
        focus_areas.extend(["Endurance", "Nutrition Practice"])
        if week_num >= 15:
            focus_areas.append("Gear Testing")
        if week_num >= 20:
            focus_areas.append("Mental Training")
    elif workout_detail == "Hill Workout":
        focus_areas.extend(["Hills", "Endurance"])
        if week_num >= 15:
            focus_areas.append("Mental Training")
    elif workout_detail == "Tempo Run":
        focus_areas.extend(["Speed", "Endurance"])
        focus_areas.append("Mental Training")
    elif workout_detail == "Easy Run":
        focus_areas.append("Endurance")
        if week_num >= 15:
            focus_areas.append("Recovery")
    elif workout_detail == "Recovery Run":
        focus_areas.append("Recovery")
    elif workout_detail == "Cross Training":
        focus_areas.append("Recovery")
        focus_areas.append("Endurance")
    elif workout_detail == "Strength Training":
        focus_areas.append("Recovery")
    elif workout_detail == "Rest Day":
        focus_areas.append("Recovery")

    # Always add focus areas
    if focus_areas:
        record["Focus Areas"] = focus_areas

    # Add pace/effort guidance for all workout types
    if workout_detail == "Long Run":
        record["Target Pace Effort"] = "10:30-11:00/mile comfortable"
    elif workout_detail == "Easy Run":
        record["Target Pace Effort"] = "10:30-11:30/mile conversational"
    elif workout_detail == "Recovery Run":
        record["Target Pace Effort"] = "11:00-12:00/mile very easy"
    elif workout_detail == "Tempo Run":
        record["Target Pace Effort"] = "9:00-9:30/mile comfortably hard"
    elif workout_detail == "Hill Workout":
        record["Target Pace Effort"] = "Sustained hard effort on climbs"
    elif workout_detail == "Cross Training":
        if week_num <= 8:
            record["Target Pace Effort"] = "Zone 2 aerobic - conversational"
        else:
            record["Target Pace Effort"] = "Moderate steady effort"
    elif workout_detail == "Strength Training":
        record["Target Pace Effort"] = "Controlled tempo, focus on form"
    elif workout_detail == "Rest Day":
        if "Yoga" in record["Name"]:
            record["Target Pace Effort"] = "Gentle, restorative pace"
        else:
            record["Target Pace Effort"] = "Complete rest"

    return record


def populate_training_plans():
    """Main function to populate all training plans."""
    logger.info("=" * 60)
    logger.info("Populating Training Plans for Beaverhead 100k")
    logger.info("=" * 60)
    logger.info(f"Race Date: {RACE_DATE.strftime('%A, %B %d, %Y')}")
    logger.info(f"Training Start: {TRAINING_START.strftime('%A, %B %d, %Y')}")
    logger.info(f"Total Weeks: 25")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        day_table = api.table(Config.AIRTABLE_BASE_ID, DAY_TABLE_ID)
        training_table = api.table(Config.AIRTABLE_BASE_ID, TRAINING_PLANS_TABLE_ID)

        # Get all day records
        logger.info("\nFetching Day records...")
        day_records = day_table.all()
        logger.info(f"Found {len(day_records)} day records")

        # Create lookup: date -> day record ID
        date_to_day = {}
        for record in day_records:
            date_str = record["fields"].get("Day")
            if date_str:
                date_to_day[date_str] = record["id"]

        logger.info(f"Mapped {len(date_to_day)} dates to day records")

        # Generate all workouts
        all_workouts = []
        total_mileage = 0
        total_elevation = 0

        logger.info("\n" + "=" * 60)
        logger.info("Generating Workouts by Phase")
        logger.info("=" * 60)

        for phase, phase_data in TRAINING_PLAN.items():
            logger.info(f"\n{phase}:")
            phase_mileage = 0
            phase_elevation = 0

            for week_num in phase_data["weeks"]:
                # Calculate week start date
                week_start = TRAINING_START + timedelta(weeks=week_num - 1)

                # Get weekly data
                weekly_mileage = phase_data["weekly_mileage"][week_num]
                long_run_data = phase_data["saturday_long_runs"][week_num]
                long_run_distance = long_run_data["distance"]

                # Calculate other distances
                other_distances = calculate_non_long_run_distances(
                    week_num, phase, weekly_mileage, long_run_distance
                )

                logger.info(f"  Week {week_num}: {weekly_mileage} miles")

                # Create workouts for each day
                for day_offset, weekday in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
                    workout_date = week_start + timedelta(days=day_offset)
                    date_str = workout_date.strftime("%Y-%m-%d")

                    # Find day record
                    if date_str not in date_to_day:
                        logger.warning(f"    No day record for {date_str} ({weekday})")
                        continue

                    day_record_id = date_to_day[date_str]

                    # Get workout structure for this day
                    workout_data = phase_data["weekly_structure"][weekday].copy()

                    # Add specific workout details
                    if weekday == "Saturday":
                        # Long run
                        workout_data["distance"] = long_run_data["distance"]
                        workout_data["elevation"] = long_run_data["elevation"]
                        workout_data["description"] = long_run_data["description"]

                        phase_mileage += long_run_data["distance"]
                        phase_elevation += long_run_data["elevation"]
                        total_mileage += long_run_data["distance"]
                        total_elevation += long_run_data["elevation"]

                    elif weekday == "Wednesday":
                        # Quality workout or easy run
                        if "wednesday_workouts" in phase_data and week_num in phase_data["wednesday_workouts"]:
                            # Specific quality workout defined
                            wed_workout = phase_data["wednesday_workouts"][week_num]
                            if "type" in wed_workout:
                                workout_data["type"] = wed_workout["type"]
                            workout_data["description"] = wed_workout["description"]
                            workout_data["elevation"] = wed_workout.get("elevation", 0)
                            workout_data["distance"] = other_distances["Wednesday"]

                            phase_mileage += other_distances["Wednesday"]
                            phase_elevation += wed_workout.get("elevation", 0)
                            total_mileage += other_distances["Wednesday"]
                            total_elevation += wed_workout.get("elevation", 0)
                        elif workout_data["type"] == "Easy Run":
                            # Base building phase - just easy run
                            workout_data["distance"] = other_distances["Wednesday"]
                            workout_data["elevation"] = int(other_distances["Wednesday"] * 60)  # ~60 ft/mile for easy hills
                            workout_data["description"] = "Easy pace on rolling hills, building aerobic base"

                            phase_mileage += other_distances["Wednesday"]
                            phase_elevation += workout_data["elevation"]
                            total_mileage += other_distances["Wednesday"]
                            total_elevation += workout_data["elevation"]

                    elif weekday == "Sunday":
                        # Check if it's a back-to-back run day
                        if "sunday_runs" in phase_data and week_num in phase_data["sunday_runs"]:
                            sunday_run = phase_data["sunday_runs"][week_num]
                            workout_data["type"] = sunday_run["type"]
                            workout_data["distance"] = sunday_run["distance"]
                            workout_data["elevation"] = sunday_run["elevation"]
                            workout_data["description"] = sunday_run["description"]

                            phase_mileage += sunday_run["distance"]
                            phase_elevation += sunday_run["elevation"]
                            total_mileage += sunday_run["distance"]
                            total_elevation += sunday_run["elevation"]

                    elif weekday in ["Tuesday", "Thursday"]:
                        # Add distance and details for runs
                        if workout_data["type"] == "Easy Run":
                            workout_data["distance"] = other_distances[weekday]
                            workout_data["elevation"] = int(other_distances[weekday] * 50)  # ~50 ft/mile average
                            workout_data["description"] = "Easy conversational pace on rolling terrain"

                            phase_mileage += other_distances[weekday]
                            phase_elevation += workout_data["elevation"]
                            total_mileage += other_distances[weekday]
                            total_elevation += workout_data["elevation"]

                        elif workout_data["type"] == "Recovery Run":
                            workout_data["distance"] = other_distances[weekday]
                            workout_data["elevation"] = int(other_distances[weekday] * 30)  # ~30 ft/mile for recovery
                            workout_data["description"] = "Very easy effort, flat to gently rolling terrain. Optional - skip if fatigued."

                            phase_mileage += other_distances[weekday]
                            phase_elevation += workout_data["elevation"]
                            total_mileage += other_distances[weekday]
                            total_elevation += workout_data["elevation"]

                    # Create workout record
                    workout_record = create_workout_record(week_num, day_record_id, weekday, workout_data, phase)
                    all_workouts.append(workout_record)

            logger.info(f"  Phase Total: {phase_mileage:.1f} miles, {phase_elevation:,} ft")

        logger.info("\n" + "=" * 60)
        logger.info(f"Total Workouts Generated: {len(all_workouts)}")
        logger.info(f"Total Mileage: {total_mileage:.1f} miles")
        logger.info(f"Total Elevation Gain: {total_elevation:,} feet")
        logger.info("=" * 60)

        # Upload to Airtable
        logger.info("\nUploading to Airtable...")
        logger.info("This will take a few minutes...")

        # Batch upload (10 at a time)
        batch_size = 10
        uploaded_count = 0

        for i in range(0, len(all_workouts), batch_size):
            batch = all_workouts[i:i + batch_size]
            try:
                training_table.batch_create(batch)
                uploaded_count += len(batch)
                logger.info(f"  Uploaded {uploaded_count}/{len(all_workouts)} workouts...")
            except Exception as e:
                logger.error(f"  Failed to upload batch {i}-{i+batch_size}: {e}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Successfully uploaded {uploaded_count} workouts")
        logger.info("\nNext steps:")
        logger.info("1. Review Training Plans in Airtable")
        logger.info("2. Adjust any workouts as needed")
        logger.info("3. Start training on January 20, 2026!")
        logger.info("\n🏔️ Let's make it to that finish line!")

        return 0

    except Exception as e:
        logger.error(f"Error populating training plans: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    return populate_training_plans()


if __name__ == "__main__":
    sys.exit(main())
