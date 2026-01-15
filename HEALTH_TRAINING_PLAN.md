# Health & Training Module - Technical Plan

## Overview

Create a Garmin → Notion sync system to track:
- ✅ Workouts/Activities (runs, rides, swims, strength training)
- ✅ Daily metrics (steps, sleep, heart rate, stress)
- ✅ Training plans (scheduled workouts)
- ✅ Body metrics (weight, body composition)

**Primary Goal**: Historical tracking for Claude to analyze trends, suggest improvements, and help plan future training.

---

## Architecture

### Module Structure
```
/Users/marykate/Desktop/personal_assistant/health-training/
├── src/
│   ├── config.py              # Configuration management
│   ├── garmin_sync.py         # Garmin Connect API client
│   ├── notion_sync.py         # Notion API operations
│   ├── state_manager.py       # SQLite state tracking
│   └── utils.py               # Logging, retry logic
├── scripts/
│   └── test_auth.py           # Test Garmin + Notion auth
├── credentials/               # OAuth credentials (gitignored)
├── logs/                      # Log files (gitignored)
├── state.db                   # State database (gitignored)
├── sync_orchestrator.py       # Main sync script
├── requirements.txt           # Python dependencies
├── .env                       # Configuration (gitignored)
├── .env.example
└── README.md
```

### Data Flow
```
Garmin Connect API
    ↓
garmin_sync.py (fetch activities, metrics, body data)
    ↓
state_manager.py (check for duplicates, track sync state)
    ↓
notion_sync.py (create/update Notion pages)
    ↓
Notion Databases (Workouts, Daily Metrics, Body Metrics)
```

---

## Notion Database Design

### 1. Workouts Database
Tracks individual training sessions.

| Property | Type | Description |
|----------|------|-------------|
| Title | Title | Activity name (e.g., "Morning Run") |
| Date | Date | When the workout occurred |
| Activity Type | Select | Run, Ride, Swim, Strength, Walk, Other |
| Duration | Number | Minutes |
| Distance | Number | Miles or km |
| Avg Heart Rate | Number | BPM |
| Max Heart Rate | Number | BPM |
| Calories | Number | kcal |
| Avg Pace | Text | min/mile or min/km |
| Elevation Gain | Number | Feet or meters |
| TSS/Intensity | Number | Training Stress Score or intensity |
| Notes | Text | Auto-populated from Garmin notes |
| External ID | Text | Garmin activity ID |
| Garmin URL | URL | Link to activity on Garmin Connect |
| Last Synced | Date | When last updated |

### 2. Daily Metrics Database
Tracks daily health summaries.

| Property | Type | Description |
|----------|------|-------------|
| Date | Title | Date (YYYY-MM-DD) |
| Steps | Number | Daily step count |
| Sleep Hours | Number | Hours of sleep |
| Sleep Quality | Select | Excellent, Good, Fair, Poor |
| Resting Heart Rate | Number | BPM |
| Avg Stress | Number | 0-100 stress score |
| Active Calories | Number | kcal |
| Total Calories | Number | kcal |
| Floors Climbed | Number | Floors |
| Body Battery | Number | 0-100 energy score (if available) |
| External ID | Text | Date-based ID |
| Last Synced | Date | When last updated |

### 3. Body Metrics Database
Tracks weight and body composition.

| Property | Type | Description |
|----------|------|-------------|
| Date | Title | Measurement date |
| Weight | Number | lbs or kg |
| BMI | Number | Body Mass Index |
| Body Fat % | Number | Percentage |
| Muscle Mass | Number | lbs or kg |
| Bone Mass | Number | lbs or kg |
| Body Water % | Number | Percentage |
| Notes | Text | Manual notes |
| External ID | Text | Date-based ID |
| Last Synced | Date | When last updated |

---

## Garmin Connect API Integration

### Authentication Options

Garmin doesn't have an official public API, but there are two approaches:

#### Option A: garth Library (Recommended)
- Python library: `garth`
- Uses Garmin Connect credentials (email/password)
- Handles authentication and token refresh
- Well-maintained and actively used

**Pros**: Simple, well-documented, actively maintained
**Cons**: Requires storing Garmin credentials (encrypted)

#### Option B: garminconnect Library
- Alternative Python library: `garminconnect`
- Similar authentication approach
- Good documentation

**Pros**: Another solid option
**Cons**: Less frequently updated than garth

### API Capabilities

Both libraries can fetch:
- ✅ Activities (workouts) with full details
- ✅ Daily summaries (steps, sleep, heart rate)
- ✅ Body composition data
- ✅ Training calendar/scheduled workouts
- ✅ Heart rate zones
- ✅ Personal records

---

## Implementation Phases

### Phase 1: MVP (Core Workout Sync)
**Goal**: Sync completed activities from Garmin to Notion

**Tasks**:
1. Set up project structure
2. Implement Garmin authentication (garth library)
3. Create Workouts database in Notion
4. Fetch recent activities from Garmin
5. Create workout pages in Notion
6. Add state management for duplicate prevention
7. Test with manual sync

**Deliverables**:
- Basic workout sync working
- Manual sync command
- Documentation

**Time estimate**: Start with this and expand

### Phase 2: Daily Metrics Sync
**Goal**: Track daily health metrics

**Tasks**:
1. Create Daily Metrics database in Notion
2. Fetch daily summaries from Garmin
3. Sync steps, sleep, heart rate, stress
4. Add incremental sync (only fetch new days)

**Deliverables**:
- Daily metrics tracking
- Historical backfill capability

### Phase 3: Body Metrics Sync
**Goal**: Track weight and body composition

**Tasks**:
1. Create Body Metrics database in Notion
2. Fetch weight/body comp from Garmin
3. Sync with duplicate detection

**Deliverables**:
- Weight tracking over time
- Body composition trends

### Phase 4: Advanced Features
**Goal**: Enhanced tracking and analysis

**Possible additions**:
- Training calendar sync (scheduled workouts)
- Gear tracking (shoes, bikes)
- Personal records
- Training load/fitness trends
- Heart rate zone analysis
- Weather data for outdoor activities

---

## Sync Strategy

### Initial Sync
- Fetch last 90 days of activities
- Fetch last 30 days of daily metrics
- Fetch last 30 days of body metrics

### Incremental Sync
- Run every 6-12 hours
- Only fetch data since last successful sync
- Use state manager to track sync tokens/timestamps

### Scheduling
```bash
# Cron job for twice-daily sync
0 7,19 * * * cd /Users/marykate/Desktop/personal_assistant/health-training && venv/bin/python sync_orchestrator.py >> logs/cron.log 2>&1
```

---

## Integration with Calendar Module

### Unified Dashboard
Create a master dashboard in Notion with:
- Calendar Events (linked database)
- Tasks (linked database)
- Workouts (linked database)
- Daily Metrics (linked database)

### Claude Use Cases

**Training Analysis**:
```
Look at my workout history for the past month.
Am I training consistently? What trends do you see?
```

**Recovery Planning**:
```
Check my recent workouts and sleep data. Do I need
a recovery day? Should I do an easy workout or rest?
```

**Schedule Integration**:
```
I want to run 4x per week. Look at my calendar and
suggest the best days/times based on my meeting schedule.
```

**Performance Tracking**:
```
Compare my running pace over the last 3 months.
Am I getting faster? What might be helping or hurting?
```

**Goal Setting**:
```
I want to run a half marathon in 3 months. Based on
my current fitness level and calendar availability,
can you suggest a training plan?
```

---

## Security Considerations

### Garmin Credentials
- Store in `.env` file (gitignored)
- Consider encryption at rest
- Session tokens cached locally
- Auto-refresh tokens when expired

### Notion Token
- Reuse existing integration from calendar-sync
- Same "Calendar Sync" integration can access all databases

---

## Technical Requirements

### Python Libraries
```
garth                    # Garmin Connect API
notion-client           # Notion API (already installed)
python-dotenv           # Environment variables (already installed)
requests                # HTTP requests (already installed)
```

### Configuration (.env)
```bash
# Garmin Connect
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_garmin_password

# Notion (reuse from calendar-sync)
NOTION_TOKEN=ntn_xxxxxxxxxxxxxxxxxxxx
NOTION_WORKOUTS_DB_ID=xxxxxxxxxxxxx
NOTION_DAILY_METRICS_DB_ID=xxxxxxxxxxxxx
NOTION_BODY_METRICS_DB_ID=xxxxxxxxxxxxx

# Sync settings
SYNC_LOOKBACK_DAYS=90
SYNC_FREQUENCY_HOURS=12
```

---

## Alternative: Strava Integration

If you use Strava as your primary platform:

**Pros**:
- Official API with OAuth
- Better documented
- More social features
- No credential storage needed

**Cons**:
- Requires syncing Garmin → Strava → Notion (two hops)
- Rate limits on API
- Less detailed metrics than Garmin

**Recommendation**: Start with Garmin direct integration. Can add Strava later if needed.

---

## Next Steps

1. **Review this plan** - Does this match your vision?
2. **Confirm Garmin setup** - Do you have a Garmin Connect account with activity history?
3. **Choose starting phase** - Start with Phase 1 (workouts only) or full implementation?
4. **Set up module** - Create directory structure and initial files

**Questions to consider**:
- Do you want metric units (km, kg) or imperial (miles, lbs)?
- How far back should we sync historical data?
- Any specific activity types you care most about?
- Do you use any other platforms (Strava, TrainingPeaks, etc.)?

---

## Estimated Effort

- **Phase 1 (MVP)**: Similar to calendar-sync Phase 1
- **Phase 2-3**: Additional databases, similar patterns
- **Total**: Could have basic sync working in one session, full system in 2-3 iterations

**My recommendation**: Start with Phase 1 (workouts only), get that working and tested, then expand to daily metrics and body metrics.

---

Ready to start building? Let me know and I'll begin implementing!
