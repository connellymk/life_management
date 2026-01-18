# Airtable Setup - Complete ✓

## Summary

Your Airtable base is now fully configured and ready for data synchronization!

## Architecture

### Dimension Tables (Existing)
- ✓ **Day** - Central date dimension (ISO format: 2026-01-17, displays as 1/17/26)
- ✓ **Week** - Weekly planning dimension (format: 3-26)
  - **NEW**: Added "Training Plan" field for weekly training overview
- ✓ Month, Quarter, Year - Additional time dimensions

### Data Tables (Newly Created with Fields)

#### 1. Calendar Events (16 fields)
Links calendar appointments from Google Calendar to Day table.

**Key Features**:
- Tracks events from multiple calendars
- Links to Day dimension for rollups
- Supports all-day and timed events
- Status tracking (Confirmed, Tentative, Cancelled)

#### 2. Training Sessions (18 fields)
Stores actual completed workouts from Garmin.

**Key Features**:
- Activity type (Running, Cycling, Swimming, etc.)
- Performance metrics (distance, pace, heart rate, elevation)
- Links to both Day and Week dimensions
- Training effect and calories
- Source tracking (Garmin, Strava, Manual)

#### 3. Training Plans (15 fields) ⭐ **RESTRUCTURED**
Stores individual planned training activities for comparison with actual sessions.

**Key Features**:
- Mirrors Training Sessions structure for easy comparison
- Planned vs Actual tracking
- Workout type and intensity
- Links to Day and Week for scheduling
- **Completed checkbox** to mark when done
- **Actual Activity link** to corresponding Training Session
- Race/Event association for goal-oriented training

**Comparison Workflow**:
```
Training Plans (planned) ←→ Training Sessions (actual)
        ↓                              ↓
   Link via "Actual Activity" field
```

#### 4. Health Metrics (19 fields)
Daily health data from Garmin (one record per day).

**Key Features**:
- Sleep tracking (duration, score, stages)
- Heart rate variability (HRV)
- Activity metrics (steps, floors, calories)
- Recovery metrics (stress, body battery, VO2 max)
- Hydration tracking

#### 5. Body Metrics (13 fields)
Body composition measurements.

**Key Features**:
- Weight and body fat percentage
- Muscle mass and BMI
- Water percentage
- Source tracking (Garmin Scale, Manual)

### Supporting Tables (Created, Fields TBD)
- Tasks
- Projects
- Classes
- Planned Meals
- Meal Plans
- Recipes
- Grocery Items
- Accounts
- Transactions
- Finance Summary
- Weekly Reviews
- Sync Logs

## Key Design Decisions

### 1. Planned vs Actual Training
**Training Plans** table structure changed from:
- ❌ Old: Multi-week program metadata (race name, total weeks, phases)
- ✅ New: Individual planned workouts that mirror Training Sessions

**Benefits**:
- Direct comparison: "I planned 6 miles at easy pace, actually ran 5.8 miles"
- Can link planned activity to actual session
- Weekly rollups show planned vs actual mileage
- Week table "Training Plan" field provides weekly overview

### 2. Date Handling
- **Storage**: ISO format (2026-01-17) for querying
- **Display**: US format (1/17/26) in Airtable UI
- **Linking**: Query Day table using ISO format, get record ID, link by ID

### 3. Dual Date Fields
Tables have BOTH:
- **Day link** - For rollups, grouping, relationships
- **Date field** - For sorting and filtering by actual date

## Next Steps

### Ready to Sync:

1. **Google Calendar → Calendar Events**
   ```bash
   python sync_google_calendar.py
   ```

2. **Garmin → Training Sessions & Health Metrics**
   ```bash
   python sync_garmin.py
   ```

### Workflow After Sync:

1. **Plan Your Week**:
   - Add records to Training Plans for upcoming week
   - Fill in Week table "Training Plan" field with overview

2. **Complete Workouts**:
   - Garmin auto-syncs to Training Sessions
   - Link Training Plans → Training Sessions via "Actual Activity"
   - Check "Completed" box on Training Plans

3. **Weekly Review**:
   - Compare planned vs actual mileage (rollup in Week table)
   - Review missed workouts
   - Adjust next week's plan

## Files Created

### Setup Scripts:
- `add_table_fields.py` - Add fields to existing tables
- `fix_missing_fields.py` - Fix link and checkbox fields
- `restructure_training_plans.py` - Update Training Plans structure

### Verification Scripts:
- `test_airtable.py` - Test connection and date utilities
- `inspect_tables.py` - Inspect table structure
- `get_table_ids.py` - Get table IDs for linking
- `verify_table_schemas.py` - Verify field completeness

### Documentation:
- `AIRTABLE_SETUP.md` - Personal Access Token setup guide
- `MANUAL_TABLE_SETUP.md` - Manual table creation guide (if needed)
- `airtable_findings.md` - Integration findings and table structure
- `airtable_structure_plan.md` - Complete base structure specification

## Configuration

### Environment Variables (.env)
```bash
AIRTABLE_ACCESS_TOKEN=pat...
AIRTABLE_BASE_ID=appKYFUTDs7tDg4Wr
AIRTABLE_DAY=Day
AIRTABLE_WEEK=Week
AIRTABLE_CALENDAR_EVENTS=Calendar Events
AIRTABLE_TRAINING_SESSIONS=Training Sessions
AIRTABLE_HEALTH_METRICS=Health Metrics
AIRTABLE_BODY_METRICS=Body Metrics
AIRTABLE_TRAINING_PLANS=Training Plans
```

### Python Modules:
- `airtable/base_client.py` - Airtable API client
- `airtable/date_utils.py` - Date conversion utilities (m/d/yy format)
- `airtable/calendar.py` - Calendar Events sync module
- `airtable/health.py` - Health & Training sync modules

## Support

For issues:
1. Check table names match exactly (case-sensitive)
2. Verify Personal Access Token has permissions to all tables
3. Ensure Day and Week tables exist with proper structure
4. Run verification scripts to diagnose issues

## Status: ✅ READY FOR DATA SYNC
