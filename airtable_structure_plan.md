# Airtable Structure Plan for Personal Assistant

## Overview
This plan outlines the Airtable base structure for integrating Garmin data, calendar events, and personal management workflows. The structure is designed to migrate from the current Notion + SQL hybrid system to a unified Airtable base while maintaining the benefits of both visual dashboards and powerful analytics.

## Architecture Strategy

**Hybrid Approach:**
- **Airtable**: Recent data (last 90 days) for visual dashboards and daily management
- **SQL Database**: Historical data (unlimited history) for long-term analytics
- **Sync Pattern**: Keep recent data synced to Airtable, archive older data to SQL

**Why Hybrid:**
- Airtable has a 100k records per base limit
- SQL provides unlimited history for multi-year analytics
- Airtable provides better visual interfaces for daily use
- SQL provides 30-500x faster queries for complex analytics

---

## Base Structure

### Core Dimension Tables

#### **Day Table**
**Purpose**: Central date dimension for all daily tracking
**Primary Key**: Date in format `d/m/yy` (e.g., "17/1/26" for January 17, 2026)
**Note**: This table should already exist in your Airtable base

**Key fields** (for reference):
- `Date ID` (Single line text, Primary) - Format: d/m/yy
- `Full Date` (Date) - Actual date value
- `Day of Week` (Formula) - Monday, Tuesday, etc.
- `Week` (Link to Week table)
- `Month` (Link to Month table) - If needed
- `Year` (Link to Year table) - If needed

#### **Week Table**
**Purpose**: Central week dimension for weekly planning and rollups
**Primary Key**: Week number with year (e.g., "2-26" for week 2 of 2026)
**Note**: This table should already exist in your Airtable base

**Key fields** (for reference):
- `Week ID` (Single line text, Primary) - Format: W-YY (e.g., "2-26")
- `Week Starting` (Date) - Monday of the week
- `Week Ending` (Date) - Sunday of the week
- `Year` (Number or Link to Year table)
- `Days` (Link to Day table) - All 7 days in the week

---

### Table 1: **Calendar Events**
**Purpose**: Sync calendar appointments and scheduled activities from Google Calendar

**Fields**:
- `Event ID` (Single line text, Primary field) - Unique identifier from Google Calendar
- `Title` (Single line text) - Event name
- `Day` (Link to Day table) - Link to date in d/m/yy format
- `Start Time` (Date with time) - Event start (keep for exact time)
- `End Time` (Date with time) - Event end (keep for exact time)
- `Duration` (Duration) - Formula: End Time - Start Time
- `Event Type` (Single select) - Meeting, Personal, Training, School, Work, Meal, Travel, etc.
- `Location` (Single line text)
- `Description` (Long text)
- `Attendees` (Long text) - Comma-separated list of attendees
- `Calendar Source` (Single select) - Personal, School, Work, etc.
- `URL` (URL) - Link back to Google Calendar event
- `Related Tasks` (Link to Tasks table)
- `Related Training Plan` (Link to Training Plans table)
- `Status` (Single select) - Scheduled, Completed, Cancelled
- `Created At` (Created time)
- `Modified At` (Last modified time)

**Notes**:
- Synced from Google Calendar API every 5-15 minutes
- Preserves manual edits in Airtable
- Uses Event ID for duplicate prevention
- Links to Day table using date in d/m/yy format (e.g., "17/1/26" for Jan 17, 2026)
- Keep both Day link and Start/End Time fields: Day for rollups/grouping, times for exact scheduling

---

### Table 2: **Tasks**
**Purpose**: Task and project management

**Fields**:
- `Task ID` (Autonumber, Primary field)
- `Task Name` (Single line text)
- `Description` (Long text)
- `Status` (Single select) - To Do, In Progress, Waiting, Done, Cancelled
- `Priority` (Single select) - High, Medium, Low
- `Due Day` (Link to Day table) - Link to date in d/m/yy format
- `Due Date` (Date) - Keep for sorting/filtering by actual date
- `Estimated Time` (Duration)
- `Actual Time` (Duration)
- `Category` (Single select) - Work, Personal, Health, Training, Admin, School, etc.
- `Class` (Link to Classes table)
- `Project` (Link to Projects table)
- `Related Events` (Link to Calendar Events table)
- `Subtasks` (Link to same table, self-referencing)
- `Parent Task` (Link to same table, self-referencing)
- `Energy Level Required` (Single select) - High, Medium, Low
- `Created At` (Created time)
- `Completed Day` (Link to Day table) - Day task was completed
- `Completed At` (Date) - Keep for exact completion timestamp

---

### Table 3: **Projects**
**Purpose**: Group related tasks and track project progress

**Fields**:
- `Project ID` (Autonumber, Primary field)
- `Project Name` (Single line text)
- `Description` (Long text)
- `Status` (Single select) - Planning, Active, On Hold, Completed, Archived
- `Start Day` (Link to Day table) - Project start date
- `Start Date` (Date) - Keep for sorting/filtering
- `Target End Day` (Link to Day table) - Target completion date
- `Target End Date` (Date) - Keep for sorting/filtering
- `Tasks` (Link to Tasks table)
- `Progress` (Percent) - Formula based on completed tasks
- `Priority` (Single select) - High, Medium, Low
- `Area` (Single select) - Work, Personal, Health, Learning, School, etc.

---

### Table 4: **Classes**
**Purpose**: Track academic courses and course-related information

**Fields**:
- `Class ID` (Autonumber, Primary field)
- `Class Name` (Single line text)
- `Course Code` (Single line text) - e.g., CSCI 101
- `Semester` (Single select) - Fall 2025, Spring 2026, etc.
- `Instructor` (Single line text)
- `Credits` (Number)
- `Grade` (Single select) - A, A-, B+, B, B-, etc.
- `Status` (Single select) - In Progress, Completed, Dropped
- `Tasks` (Link to Tasks table)
- `Calendar Events` (Link to Calendar Events table)
- `Description` (Long text)
- `Office Hours` (Long text)
- `Syllabus URL` (URL)

---

### Table 5: **Training Plans**
**Purpose**: Plan and track detailed training programs (e.g., marathon, ultramarathon training)

**Fields**:
- `Workout ID` (Autonumber, Primary field)
- `Name` (Single line text) - Workout name/identifier
- `Day` (Link to Day table) - Scheduled workout date in d/m/yy format
- `Date` (Date) - Keep for sorting/filtering by actual date
- `Week` (Link to Week table) - Link to week (e.g., "2-26")
- `Week Number` (Number) - Training week within plan (1-25 for ultramarathon, etc.)
- `Day of Week` (Formula) - Lookup from Day table
- `Training Phase` (Single select)
  - Base Building (green)
  - Build 1 (blue)
  - Build 2 (purple)
  - Peak (red)
  - Taper (orange)
- `Workout Type` (Single select)
  - Long Run (red)
  - Easy Run (green)
  - Tempo Run (orange)
  - Hill Workout (brown)
  - Intervals (purple)
  - Recovery Run (blue)
  - Strength Training (yellow)
  - Cross Training (gray)
  - Rest Day (default)
- `Status` (Single select)
  - Planned (gray)
  - Completed (green)
  - Skipped (yellow)
  - Modified (blue)
  - Missed (red)
- `Priority` (Single select)
  - Key Workout (red)
  - Important (orange)
  - Standard (blue)
  - Optional (gray)
- `Planned Distance` (Number) - Miles or kilometers
- `Planned Duration` (Number) - Minutes
- `Planned Elevation Gain` (Number) - Feet or meters
- `Target Pace Effort` (Single line text) - Pace or effort zone description
- `Workout Description` (Long text) - Detailed instructions
- `Workout Notes` (Long text) - Post-workout reflections
- `Focus Areas` (Multiple select)
  - Endurance (blue)
  - Speed (red)
  - Hills (brown)
  - Recovery (green)
  - Nutrition Practice (orange)
  - Gear Testing (purple)
  - Mental Training (pink)
- `Weekly Mileage Target` (Number) - Miles
- `Weekly Elevation Target` (Number) - Feet
- `Completed Workout` (Link to Training Sessions table)
- `Calendar Event` (Link to Calendar Events table)
- `Daily Metrics` (Link to Health Metrics table)

**Notes**:
- This table structure matches the existing Notion "Training Plan - Beaverhead 100k" database
- Example: 25-week ultramarathon training plan with 5 phases
- Links to actual completed workouts from Garmin via Training Sessions table

---

### Table 6: **Training Sessions** (Garmin Activities)
**Purpose**: Track completed workouts and physical activities from Garmin

**Fields**:
- `Activity ID` (Single line text, Primary field) - Unique ID from Garmin
- `Activity Name` (Single line text)
- `Activity Type` (Single select) - Running, Cycling, Swimming, Strength, Yoga, Walking, Hiking, etc.
- `Day` (Link to Day table) - Activity date in d/m/yy format
- `Week` (Link to Week table) - Link to week (e.g., "2-26")
- `Start Time` (Date with time) - Keep for exact start time
- `Duration` (Duration)
- `Distance` (Number) - Miles or kilometers
- `Calories` (Number)
- `Average HR` (Number) - Beats per minute
- `Max HR` (Number) - Beats per minute
- `Average Pace` (Number) - Minutes per mile (e.g., 8.5 for 8:30/mile)
- `Average Speed` (Number) - Miles per hour or km/h
- `Elevation Gain` (Number) - Feet or meters
- `Garmin Link` (URL) - Direct link to activity on Garmin Connect
- `Notes` (Long text) - Manual notes and reflections
- `Related Event` (Link to Calendar Events table)
- `Training Plan` (Link to Training Plans table)
- `Synced At` (Last modified time)

**Notes**:
- Synced from Garmin Connect API (last 90 days in Airtable)
- Older activities archived to SQL database for historical analysis
- Activity Type mapped from Garmin activity types
- Average Pace calculated as Duration / Distance for running/cycling

---

### Table 7: **Health Metrics** (Daily Garmin Data)
**Purpose**: Track daily health and wellness metrics from Garmin

**Fields**:
- `Day` (Link to Day table, Primary field) - Date in d/m/yy format
- `Date` (Date) - Keep for sorting/filtering by actual date
- `Resting HR` (Number) - Beats per minute
- `HRV` (Number) - Heart Rate Variability (milliseconds)
- `Sleep Duration` (Duration) - Total sleep time
- `Deep Sleep` (Duration)
- `REM Sleep` (Duration)
- `Light Sleep` (Duration)
- `Awake Time` (Duration) - Time awake during sleep period
- `Sleep Score` (Number) - 0-100
- `Steps` (Number)
- `Floors Climbed` (Number)
- `Active Calories` (Number)
- `Total Calories` (Number)
- `Intensity Minutes` (Number) - Total moderate + vigorous
- `Moderate Intensity Minutes` (Number)
- `Vigorous Intensity Minutes` (Number)
- `Stress Level` (Number) - Average stress (0-100)
- `Max Stress` (Number) - Peak stress level
- `Body Battery` (Number) - Energy level (0-100)
- `Hydration` (Number) - Glasses of water (manual tracking)
- `Notes` (Long text)
- `Synced At` (Last modified time)

**Notes**:
- Synced daily from Garmin Connect API
- Last 90 days in Airtable, older data in SQL database
- Sleep data synced from previous night
- Some fields may be null if not tracked by Garmin device

---

### Table 8: **Body Metrics**
**Purpose**: Track body composition and weight over time from Garmin scale

**Fields**:
- `Measurement ID` (Autonumber, Primary field)
- `Day` (Link to Day table) - Measurement date in d/m/yy format
- `Date` (Date) - Keep for sorting/filtering
- `Time` (Date with time) - Exact timestamp of measurement
- `Weight` (Number) - Pounds or kilograms
- `BMI` (Number) - Body Mass Index
- `Body Fat %` (Number) - Percentage
- `Muscle Mass` (Number) - Pounds or kilograms
- `Bone Mass` (Number) - Pounds or kilograms
- `Body Water %` (Number) - Percentage
- `Notes` (Long text)
- `Synced At` (Last modified time)

**Notes**:
- Synced from Garmin Connect API when scale measurements available
- May have multiple measurements per day
- Some fields may be null depending on scale capabilities

---

### Table 9: **Planned Meals** (Join Table)
**Purpose**: Link meal plans to specific recipes for each day and meal

**Fields**:
- `Entry ID` (Autonumber, Primary field)
- `Meal Plan` (Link to Meal Plans table)
- `Day` (Link to Day table) - Meal date in d/m/yy format
- `Date` (Date) - Keep for sorting/filtering
- `Day of Week` (Formula) - Lookup from Day table
- `Meal Type` (Single select) - Breakfast, Lunch, Dinner, Snack
- `Recipe` (Link to Recipes table)
- `Notes` (Long text)
- `Completed` (Checkbox)

**Notes**:
- Replaces the inflexible 21-field approach from original plan
- More scalable and easier to query
- One record per meal (not per week)

---

### Table 10: **Meal Plans**
**Purpose**: Plan meals for the week ahead

**Fields**:
- `Plan ID` (Autonumber, Primary field)
- `Week` (Link to Week table) - Link to week (e.g., "2-26")
- `Week Starting` (Date) - Keep for sorting/filtering (Monday)
- `Week Ending` (Formula) - Week Starting + 6 days
- `Status` (Single select) - Planning, Active, Completed
- `Planned Meals` (Link to Planned Meals table)
- `Shopping List` (Long text)
- `Budget` (Currency)
- `Notes` (Long text)
- `Created At` (Created time)

**Notes**:
- Uses Planned Meals join table for flexibility
- Each week is one record
- Shopping list can be auto-generated from recipes

---

### Table 11: **Recipes**
**Purpose**: Store meal recipes for planning and prep

**Fields**:
- `Recipe ID` (Autonumber, Primary field)
- `Recipe Name` (Single line text)
- `Description` (Long text)
- `Ingredients` (Long text)
- `Instructions` (Long text)
- `Prep Time` (Duration)
- `Cook Time` (Duration)
- `Total Time` (Formula) - Prep + Cook
- `Servings` (Number)
- `Meal Type` (Multiple select) - Breakfast, Lunch, Dinner, Snack
- `Cuisine` (Single select) - Italian, Mexican, Asian, American, etc.
- `Dietary Tags` (Multiple select) - Vegetarian, Vegan, Gluten-Free, Dairy-Free, etc.
- `Calories per Serving` (Number)
- `Protein per Serving` (Number)
- `Carbs per Serving` (Number)
- `Fat per Serving` (Number)
- `Photo` (Attachment)
- `Rating` (Rating) - 1-5 stars
- `Source` (URL) - Link to original recipe
- `Last Made Day` (Link to Day table) - Most recent day recipe was made
- `Last Made` (Date) - Keep for sorting/filtering
- `Times Made` (Count) - Rollup from Planned Meals
- `Favorite` (Checkbox)
- `Notes` (Long text)

---

### Table 12: **Grocery Items**
**Purpose**: Track grocery shopping and meal prep ingredients

**Fields**:
- `Item ID` (Autonumber, Primary field)
- `Item Name` (Single line text)
- `Category` (Single select) - Produce, Protein, Dairy, Grains, Pantry, Frozen, Beverages, etc.
- `Quantity` (Number)
- `Unit` (Single select) - lbs, oz, units, gallons, etc.
- `Needed For` (Link to Recipes table)
- `Meal Plan` (Link to Meal Plans table)
- `Week` (Link to Week table) - Shopping week
- `Purchased` (Checkbox)
- `Store` (Single select) - Whole Foods, Trader Joes, Costco, etc.
- `Price` (Currency)
- `Date Added` (Created time)
- `Day Purchased` (Link to Day table) - Day item was purchased
- `Date Purchased` (Date) - Keep for sorting/filtering
- `Notes` (Long text)

---

### Table 13: **Accounts** (Financial)
**Purpose**: Track bank accounts, credit cards, and investment accounts

**Fields**:
- `Account ID` (Single line text, Primary field) - From Plaid
- `Account Name` (Single line text)
- `Institution` (Single line text) - Bank name
- `Account Type` (Single select) - Checking, Savings, Credit Card, Investment, etc.
- `Account Subtype` (Single line text) - More specific type from Plaid
- `Mask` (Single line text) - Last 4 digits of account number
- `Currency` (Single select) - USD, EUR, etc.
- `Current Balance` (Currency) - Latest balance
- `Available Balance` (Currency) - Available for spending/withdrawal
- `Credit Limit` (Currency) - For credit cards
- `Status` (Single select) - Active, Closed, Error
- `Last Synced Day` (Link to Day table) - Day of last sync
- `Last Synced` (Date with time) - Keep for exact timestamp
- `Created At` (Created time)

**Notes**:
- Synced from Plaid API
- Full account numbers NEVER stored (security)
- Encrypted access tokens stored in SQL database

---

### Table 14: **Transactions** (Financial - Summary View)
**Purpose**: Track recent financial transactions (last 90 days visible in Airtable)

**Fields**:
- `Transaction ID` (Single line text, Primary field) - From Plaid
- `Account` (Link to Accounts table)
- `Day` (Link to Day table) - Transaction date in d/m/yy format
- `Date` (Date) - Keep for sorting/filtering
- `Description` (Single line text) - Merchant name
- `Amount` (Currency) - Positive for income, negative for expenses
- `Category` (Single select) - Food & Dining, Shopping, Bills, Travel, etc.
- `Subcategory` (Single line text)
- `Pending` (Checkbox)
- `Notes` (Long text)
- `Synced At` (Last modified time)

**Notes**:
- Only last 90 days synced to Airtable for visual dashboard
- Full transaction history stored in SQL database (unlimited)
- SQL provides faster analytics for historical trends

---

### Table 15: **Finance Summary** (Monthly Rollups)
**Purpose**: Track monthly financial summaries and net worth snapshots

**Fields**:
- `Summary ID` (Autonumber, Primary field)
- `Month` (Single select) - January, February, etc.
- `Year` (Number)
- `Period` (Formula) - "YYYY-MM" for sorting
- `Total Income` (Currency) - Rollup from transactions
- `Total Expenses` (Currency) - Rollup from transactions
- `Net Income` (Formula) - Income - Expenses
- `Net Worth` (Currency) - Sum of all account balances
- `Savings Rate` (Percent) - Formula
- `Top Spending Category` (Single line text)
- `Notes` (Long text)

**Notes**:
- Auto-calculated from Transactions and Accounts tables
- Provides monthly snapshot without querying full transaction history
- Can be synced from SQL database analytics

---

### Table 16: **Weekly Reviews**
**Purpose**: Track weekly planning and reflection

**Fields**:
- `Week` (Link to Week table, Primary field) - Link to week (e.g., "2-26")
- `Week Starting` (Date) - Keep for sorting/filtering (Monday)
- `Week Ending` (Formula) - Week Starting + 6 days
- `Goals for Week` (Long text)
- `Key Accomplishments` (Long text)
- `Training Summary` (Long text)
- `Total Training Time` (Rollup from Training Sessions)
- `Total Training Distance` (Rollup from Training Sessions)
- `Total Training Sessions` (Count from Training Sessions)
- `Tasks Completed` (Count from Tasks)
- `Average Sleep` (Rollup from Health Metrics)
- `Average Stress` (Rollup from Health Metrics)
- `Average Steps` (Rollup from Health Metrics)
- `Challenges` (Long text)
- `Lessons Learned` (Long text)
- `Next Week Focus` (Long text)
- `Energy Level` (Rating) - 1-5 stars
- `Overall Rating` (Rating) - 1-5 stars
- `Created At` (Created time)

**Notes**:
- One record per week
- Can be auto-created every Sunday via automation
- Rollups automatically calculate from linked records

---

### Table 17: **Sync Logs**
**Purpose**: Track integration sync status and errors

**Fields**:
- `Log ID` (Autonumber, Primary field)
- `Integration` (Single select) - Google Calendar, Garmin, Plaid, etc.
- `Sync Type` (Single select) - Calendar Events, Training Sessions, Health Metrics, Transactions, etc.
- `Started At` (Date with time)
- `Completed At` (Date with time)
- `Duration` (Formula) - Completed - Started
- `Status` (Single select) - Success, Failed, Partial
- `Records Synced` (Number)
- `Records Created` (Number)
- `Records Updated` (Number)
- `Records Skipped` (Number)
- `Error Message` (Long text)
- `Details` (Long text)

**Notes**:
- One record per sync operation
- Helps track integration health and troubleshoot issues
- Can alert if sync hasn't run in expected timeframe

---

## Data Relationships Hierarchy

```
            DAY TABLE (Central Date Dimension: d/m/yy format)
                 ↓ (links from all date-based tables)
    ┌────────────┼────────────┬─────────────┬──────────────┐
    ↓            ↓            ↓             ↓              ↓
Calendar    Training     Health      Body Metrics   Transactions
Events      Sessions     Metrics
    ↓            ↓
 Tasks      Training Plans
    ↓
Projects
    ↓
Classes


           WEEK TABLE (Central Week Dimension: W-YY format)
                 ↓ (links from all week-based tables)
    ┌────────────┼────────────┬─────────────┐
    ↓            ↓            ↓             ↓
Training     Training    Meal Plans   Weekly Reviews
Sessions      Plans                    (rollups from linked tables)
                            ↓
                      Planned Meals → Recipes
                            ↓
                      Grocery Items


Financial Hierarchy:
Accounts → Transactions → Finance Summary
```

**Key Relationships:**
- **Day table**: Central hub for all daily data (calendar events, training sessions, health metrics, body metrics, transactions, tasks)
- **Week table**: Central hub for weekly planning and rollups (training sessions, training plans, meal plans, weekly reviews, grocery lists)
- All date fields link to Day table (format: "17/1/26")
- All week fields link to Week table (format: "2-26")
- Day of week is calculated via formula from Day table (no manual entry needed)
- Rollups and aggregations flow through Day/Week tables for powerful analytics

### Benefits of Day/Week Dimension Tables

**Why use dimension tables instead of raw dates?**

1. **Centralized Date Logic**
   - Day of week calculated once in Day table, not in every table
   - Week assignment automatic through Day → Week relationship
   - Easy to add holidays, special days, or custom date attributes

2. **Powerful Rollups & Aggregations**
   - Weekly Reviews can rollup ALL data for a week through Week table
   - Daily summaries can aggregate across all activities for a day
   - No complex date filtering formulas needed

3. **Consistent Date Formatting**
   - Primary key format (d/m/yy) prevents duplicate day records
   - Week ID format (W-YY) prevents duplicate week records
   - Easy to reference in automation and formulas

4. **Better Performance**
   - Linking to Day/Week is faster than date calculations
   - Rollups through links are more efficient than filtered rollups
   - Reduces formula complexity across the base

5. **Flexibility**
   - Keep both link (for relationships) and date (for sorting/filtering)
   - Can add Month, Quarter, Year tables later if needed
   - Easy to extend with custom time periods (training cycles, sprints, etc.)

**Example Use Cases:**
- Weekly Review can link to Week → automatically get all Training Sessions, Health Metrics, and Tasks for that week via rollups
- Day table can show all events, workouts, meals, and metrics for any given day
- Training Plans can group by Week to show weekly mileage targets
- Meal Plans automatically populate 7 days through Week → Day relationship

---

## Integration Architecture

### Garmin Integration Points

**Training Sessions Sync**:
- **API**: Garmin Connect API (via `garth` Python library)
- **Sync Frequency**: Twice daily (7 AM, 7 PM) or after activity completion
- **Data Flow**: Garmin → Airtable Training Sessions table (last 90 days)
- **Data Flow**: Garmin → SQL database (all history)
- **Key Fields**: Activity ID, Type, Duration, Distance, Heart Rate, Calories, Pace, Speed
- **Current Status**: ✅ Working in Python (Notion + SQL)

**Health Metrics Sync**:
- **API**: Garmin Connect Health API (via `garth`)
- **Sync Frequency**: Daily (morning)
- **Data Flow**: Garmin → Airtable Health Metrics table (last 90 days)
- **Data Flow**: Garmin → SQL database (all history)
- **Key Fields**: Date, Sleep data, Steps, Heart Rate, Stress, Body Battery, Intensity Minutes
- **Current Status**: ✅ Working in Python (SQL)

**Body Metrics Sync**:
- **API**: Garmin Connect API
- **Sync Frequency**: Daily or when measurements taken
- **Data Flow**: Garmin → Airtable Body Metrics table (last 90 days)
- **Data Flow**: Garmin → SQL database (all history)
- **Key Fields**: Date, Weight, BMI, Body Fat %, Muscle Mass
- **Current Status**: ✅ Working in Python (SQL)

### Calendar Integration Points

**Events Sync**:
- **API**: Google Calendar API
- **Sync Frequency**: Every 5-15 minutes (bidirectional optional)
- **Data Flow**: Google Calendar ↔ Airtable Calendar Events table
- **Key Fields**: Event ID, Title, Start/End Time, Description, Attendees, Calendar Source
- **Current Status**: ✅ Working in Python (Notion)
- **Features**:
  - Multi-calendar support (Personal, School, Work)
  - Incremental sync with state management
  - Preserves manual edits in Airtable
  - Duplicate prevention

**Training Plans to Calendar**:
- Create calendar events for planned training sessions
- Update calendar when training is completed
- Sync actual vs planned times
- Link back to Training Plans table

### Financial Integration Points

**Plaid Banking Sync**:
- **API**: Plaid API (via `plaid-python` library)
- **Sync Frequency**: Daily (7 AM)
- **Data Flow**: Plaid → SQL database (all transactions)
- **Data Flow**: SQL → Airtable (last 90 days for dashboard)
- **Security**: Encrypted tokens, masked account numbers, local storage only
- **Current Status**: ✅ Working in Python (SQL)
- **Features**:
  - Bank accounts, credit cards, investments
  - Unlimited transaction history in SQL
  - Daily balance snapshots for net worth tracking
  - Category-based spending analysis

---

## Views and Workflows

### Recommended Views Per Table

**Calendar Events**:
- **Calendar View** - Visual calendar by Start Time
- **Grid by Event Type** - Grouped by Meeting, Personal, Training, School, etc.
- **This Week** - Filtered to current week
- **Upcoming** - Next 14 days
- **Training Events Only** - Filtered by Event Type = Training
- **School Schedule** - Filtered by Calendar Source = School

**Tasks**:
- **Kanban by Status** - To Do, In Progress, Waiting, Done
- **Grid by Priority** - Grouped by High, Medium, Low
- **This Week** - Due Date within current week
- **By Project** - Grouped by Project
- **By Class** - Grouped by Class
- **By Energy Level** - Grouped by energy required

**Classes**:
- **Current Semester** - Filtered by Status = In Progress
- **All Classes** - Grid view
- **By Semester** - Grouped by Semester

**Training Plans**:
- **Current Week** - Filtered by Week Number
- **Training Phase Board** - Kanban grouped by Training Phase
- **Weekly Summary** - Grouped by Week Number with totals
- **Key Workouts Only** - Filtered by Priority = "Key Workout"
- **Completed vs Planned** - Filtered by Status
- **Calendar View** - Visual calendar by Date

**Training Sessions**:
- **Calendar View** - Visual calendar by Start Time
- **By Activity Type** - Grouped by Running, Cycling, etc.
- **This Week** - Last 7 days
- **This Month** - Last 30 days
- **Recent Activities** - Sorted by date descending

**Health Metrics**:
- **Grid by Date** - Chronological view
- **Last 7 Days** - Filtered and sorted
- **Last 30 Days** - For monthly trends
- **Trends** - For charts and graphs
- **Low Sleep Alert** - Filtered by Sleep Duration < 6 hours

**Body Metrics**:
- **Chronological** - Grid by Date
- **Last 30 Days** - Recent measurements
- **Weight Trend** - Chart view

**Meal Plans**:
- **Current Week** - This week's plan
- **All Plans** - Grid view
- **By Week** - Grouped by Week Starting

**Planned Meals**:
- **This Week** - Current week's meals
- **By Day** - Grouped by Day of Week
- **By Meal Type** - Grouped by Breakfast, Lunch, Dinner

**Accounts**:
- **Active Accounts** - Filtered by Status = Active
- **By Institution** - Grouped by bank name
- **By Account Type** - Grouped by Checking, Savings, etc.

**Transactions**:
- **Recent** - Last 30 days, sorted by date descending
- **By Category** - Grouped by spending category
- **By Account** - Grouped by account
- **Large Transactions** - Filtered by Amount > $100

**Finance Summary**:
- **Year to Date** - Current year
- **Trend** - Chronological chart
- **Grid by Month** - All months

**Weekly Reviews**:
- **Recent Reviews** - Last 8 weeks
- **All Reviews** - Grid view
- **By Rating** - Sorted by Overall Rating

---

## Automation Ideas

### High Priority (Implement First)

1. **Auto-sync from Garmin** (via Python script)
   - Training Sessions sync twice daily
   - Health Metrics sync daily
   - Body Metrics sync when available

2. **Auto-sync from Google Calendar** (via Python script)
   - Every 5-15 minutes for real-time updates
   - Incremental sync with state management

3. **Weekly Review Auto-Creation**
   - Every Sunday evening, create new weekly review record
   - Auto-populate rollup fields from Training Sessions, Health Metrics, Tasks

### Medium Priority

4. **Training Load Monitoring**
   - Alert if weekly training distance increases > 10% week-over-week
   - Flag potential overtraining based on distance + stress levels

5. **Health Metrics Alerts**
   - If Sleep Duration < 6 hours, flag in Weekly Review
   - If Average Stress > 70, suggest recovery day

6. **Task Due Date Reminders**
   - Move to High Priority if Due Date within 2 days
   - Send notification via Airtable automation

### Low Priority (Nice to Have)

7. **Auto-create Calendar Events from Training Plans**
   - When Training Plan workout created, add to Google Calendar
   - Sync actual completion back to Training Plan

8. **Meal Plan to Grocery List**
   - When Planned Meals added, auto-populate Grocery Items
   - Extract ingredients from linked Recipes

9. **Schedule Optimization**
   - Suggest best times for tasks based on Energy Level and Calendar gaps
   - Avoid scheduling high-energy tasks during busy meeting days

10. **Finance Category Auto-Tagging**
    - Use Plaid categories by default
    - Learn from manual corrections to improve future categorization

---

## Migration Strategy from Notion + SQL

### Phase 1: Setup Airtable Base
1. Create Airtable base with all tables and fields
2. Configure views for each table
3. Set up automations for weekly reviews and alerts

### Phase 2: Migrate Python Integration Code
1. Update `core/config.py` to include Airtable credentials
   - Add `AIRTABLE_API_KEY`
   - Add `AIRTABLE_BASE_ID`
   - Add table IDs for each Airtable table
2. Create `airtable/` module with CRUD operations
   - `airtable/calendar.py` - Calendar Events operations
   - `airtable/health.py` - Training Sessions, Health Metrics, Body Metrics
   - `airtable/tasks.py` - Tasks, Projects, Classes
   - `airtable/finance.py` - Accounts, Transactions, Finance Summary
3. Update orchestrators to use Airtable instead of Notion
   - `orchestrators/sync_calendar.py` - Use Airtable
   - `orchestrators/sync_health.py` - Use Airtable for recent data
   - Keep SQL database for historical data

### Phase 3: Data Migration
1. Export existing Notion data
2. **Prepare Day/Week table lookups**
   - Ensure Day table populated with all dates needed (auto-generate if needed)
   - Ensure Week table populated with all weeks needed
   - Create helper function to convert dates to Day ID format (d/m/yy)
   - Create helper function to convert dates to Week ID format (W-YY)
3. Import to Airtable via API
   - For each record with a date field, convert to Day ID and link to Day table
   - For each record with a week reference, convert to Week ID and link to Week table
   - Maintain external IDs for continuity (Event ID, Activity ID, etc.)
4. Verify data integrity
   - Check all Day/Week links are valid
   - Verify rollups calculate correctly through Week table
   - Test day of week formulas lookup correctly from Day table
5. Test syncs end-to-end

### Phase 4: Hybrid SQL + Airtable
1. Keep SQL database for:
   - All transactions (unlimited history)
   - Health metrics history (> 90 days)
   - Body metrics history (> 90 days)
   - Training sessions history (> 90 days)
2. Sync to Airtable:
   - Last 90 days of transactions for dashboard
   - Last 90 days of health/body/training data for visual tracking
3. Monthly archive job:
   - Move older Airtable records to SQL database
   - Keep Airtable under 100k record limit

### Phase 5: Dashboard & Analytics
1. Create Airtable interfaces for:
   - Daily dashboard (calendar, tasks, recent workouts)
   - Weekly planning (upcoming week overview)
   - Training dashboard (workout log, health trends)
   - Financial dashboard (spending, net worth)
2. Connect Claude AI to:
   - Airtable API for recent data queries
   - SQL database for historical analytics
   - Combined insights across both systems

---

## Technical Notes for Integration

### Airtable API

**Authentication**:
- **Personal Access Token (PAT)** - Recommended by Airtable
  - Get from: https://airtable.com/create/tokens
  - Required scopes: `data.records:read`, `data.records:write`, `schema.bases:read`
  - Store in `.env` file as `AIRTABLE_ACCESS_TOKEN`
  - Tokens can be scoped to specific bases and have expiration dates
- Legacy API Key (deprecated by Airtable, not recommended for new integrations)

**Base & Table IDs**:
- Base ID: Found in Airtable API documentation for your base
- Table IDs: Can be found in API docs or via API
- Store in `.env` file for each table

**Creating a Personal Access Token**:
1. Go to https://airtable.com/create/tokens
2. Click "Create new token"
3. Name your token (e.g., "Personal Assistant Sync")
4. Add scopes:
   - `data.records:read` - Read records
   - `data.records:write` - Create/update records
   - `schema.bases:read` - Read base schema
5. Add access to your specific base
6. Copy the token (starts with `pat_`) - you won't be able to see it again!
7. Store in your `.env` file as `AIRTABLE_ACCESS_TOKEN`

**Rate Limits**:
- 5 requests per second per base
- 100,000 records per base (total across all tables)
- Use batch operations where possible

**Python Library**:
```python
# Install
pip install pyairtable

# Usage
from pyairtable import Api
api = Api(api_key)
table = api.table(base_id, table_name)

# Create record
table.create({'Field Name': 'value'})

# Update record
table.update(record_id, {'Field Name': 'new value'})

# Get all records
records = table.all()
```

### Recommended Python Libraries

```python
# requirements.txt additions
pyairtable>=2.0.0        # Airtable API client
garth>=0.4.0             # Garmin Connect API
google-api-python-client>=2.0.0  # Google Calendar API
plaid-python>=14.0.0     # Plaid Banking API
python-dotenv>=1.0.0     # Environment variables
tenacity>=8.2.0          # Retry logic
cryptography>=41.0.0     # Secure token storage
```

### Date Conversion Utilities

**Helper functions for Day/Week table integration:**

```python
from datetime import datetime, timedelta

def date_to_day_id(date_obj):
    """
    Convert a date object to Day table ID format (d/m/yy).

    Args:
        date_obj: datetime object or date string

    Returns:
        str: Date in d/m/yy format (e.g., "17/1/26")
    """
    if isinstance(date_obj, str):
        date_obj = datetime.fromisoformat(date_obj)

    return date_obj.strftime("%-d/%-m/%y")  # Unix/Mac
    # For Windows: return date_obj.strftime("%#d/%#m/%y")


def date_to_week_id(date_obj):
    """
    Convert a date object to Week table ID format (W-YY).

    Args:
        date_obj: datetime object or date string

    Returns:
        str: Week in W-YY format (e.g., "2-26" for week 2 of 2026)
    """
    if isinstance(date_obj, str):
        date_obj = datetime.fromisoformat(date_obj)

    week_num = date_obj.isocalendar()[1]  # ISO week number
    year = date_obj.strftime("%y")

    return f"{week_num}-{year}"


def get_week_starting_monday(date_obj):
    """
    Get the Monday of the week for a given date.

    Args:
        date_obj: datetime object or date string

    Returns:
        datetime: Monday of the week
    """
    if isinstance(date_obj, str):
        date_obj = datetime.fromisoformat(date_obj)

    # Get the Monday of the week (weekday: 0=Monday, 6=Sunday)
    days_since_monday = date_obj.weekday()
    monday = date_obj - timedelta(days=days_since_monday)

    return monday


# Example usage in sync script:
def sync_calendar_event_to_airtable(event, airtable_table):
    """Sync a Google Calendar event to Airtable with Day table link."""
    start_time = datetime.fromisoformat(event['start']['dateTime'])
    day_id = date_to_day_id(start_time)

    record = {
        'Event ID': event['id'],
        'Title': event['summary'],
        'Day': [day_id],  # Link to Day table by ID
        'Start Time': start_time.isoformat(),
        'End Time': event['end']['dateTime'],
        # ... other fields
    }

    airtable_table.create(record)


def sync_training_session_to_airtable(activity, airtable_table):
    """Sync a Garmin activity to Airtable with Day and Week table links."""
    start_time = datetime.fromisoformat(activity['startTimeLocal'])
    day_id = date_to_day_id(start_time)
    week_id = date_to_week_id(start_time)

    record = {
        'Activity ID': str(activity['activityId']),
        'Activity Name': activity['activityName'],
        'Day': [day_id],  # Link to Day table
        'Week': [week_id],  # Link to Week table
        'Start Time': start_time.isoformat(),
        'Duration': activity['duration'],
        # ... other fields
    }

    airtable_table.create(record)
```

### Data Sync Strategy

**Duplicate Prevention**:
- Use external IDs as primary keys (Event ID, Activity ID, Transaction ID, etc.)
- Maintain state database (SQLite) to track last sync timestamp per integration
- Check for existing records before creating new ones

**Error Handling**:
- Retry failed API calls with exponential backoff (via `tenacity`)
- Log all sync operations to Sync Logs table
- Alert on consecutive failures

**Incremental Sync**:
- Store `last_sync_timestamp` in state database
- Only query/sync records modified since last sync
- Reduces API calls and improves performance

**Batch Operations**:
- Use Airtable batch create/update (up to 10 records per call)
- Reduces API calls and stays under rate limits
- Important for initial sync of large datasets

**Logging**:
- Log all sync operations with timestamps
- Record counts (created, updated, skipped)
- Error messages and stack traces
- Store in `logs/sync.log` and Sync Logs table

---

## Configuration Example

**`.env` file additions**:
```bash
# Airtable
# Personal Access Token (recommended) - get from https://airtable.com/create/tokens
AIRTABLE_ACCESS_TOKEN=pat_your_personal_access_token_here
# Legacy API Key (deprecated)
# AIRTABLE_API_KEY=key_your_api_key_here
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX

# Airtable Table Names (Dimension Tables)
AIRTABLE_DAY=Day
AIRTABLE_WEEK=Week

# Airtable Table Names (Data Tables)
AIRTABLE_CALENDAR_EVENTS=Calendar Events
AIRTABLE_TASKS=Tasks
AIRTABLE_PROJECTS=Projects
AIRTABLE_CLASSES=Classes
AIRTABLE_TRAINING_PLANS=Training Plans
AIRTABLE_TRAINING_SESSIONS=Training Sessions
AIRTABLE_HEALTH_METRICS=Health Metrics
AIRTABLE_BODY_METRICS=Body Metrics
AIRTABLE_PLANNED_MEALS=Planned Meals
AIRTABLE_MEAL_PLANS=Meal Plans
AIRTABLE_RECIPES=Recipes
AIRTABLE_GROCERY_ITEMS=Grocery Items
AIRTABLE_ACCOUNTS=Accounts
AIRTABLE_TRANSACTIONS=Transactions
AIRTABLE_FINANCE_SUMMARY=Finance Summary
AIRTABLE_WEEKLY_REVIEWS=Weekly Reviews
AIRTABLE_SYNC_LOGS=Sync Logs

# Keep existing Garmin, Google Calendar, Plaid configs
# Keep existing SQL database configs
```

---

## Next Steps

### Immediate Actions
1. ✅ **Review this refined plan** - Verify all tables and fields match your needs
2. **Set up Airtable base** - Create tables with fields as specified above
3. **Configure views** - Set up recommended views for each table
4. **Add sample data** - Test with a few records to verify structure

### Development Tasks
5. **Install pyairtable** - Add to requirements.txt and install
6. **Create Airtable module** - Build CRUD operations for each table
7. **Update configuration** - Add Airtable credentials to .env
8. **Migrate orchestrators** - Update sync scripts to use Airtable API

### Testing & Deployment
9. **Test sync workflows** - Start with one integration (e.g., Calendar)
10. **Migrate existing data** - Import current Notion data to Airtable
11. **Build automations** - Implement weekly reviews, alerts, etc.
12. **Create dashboard** - Build Airtable interfaces for daily use

### Optimization
13. **Set up hybrid archival** - Move old data from Airtable to SQL
14. **Performance tuning** - Optimize batch operations and API calls
15. **Create analytics views** - Build SQL queries for historical analysis
16. **Connect Claude AI** - Enable AI-powered insights across both systems

---

## Performance Expectations

**Calendar Sync** (Airtable):
- First sync: ~3-5 minutes (350+ events with duplicate checking)
- Subsequent syncs: ~3-5 seconds (incremental with state management)
- Recommended: Every 5-15 minutes (automated)

**Health Sync** (Hybrid Airtable + SQL):
- First sync: ~5-6 minutes (42 workouts to Airtable)
- Daily metrics: <1 second to SQL (30x faster than API)
- Airtable sync (last 90 days): ~10-15 seconds
- Subsequent syncs: ~10-15 seconds (workouts) + <1 second (metrics)
- Recommended: Twice daily or on-demand

**Financial Sync** (Hybrid SQL + Airtable):
- First sync: ~5-10 seconds (accounts + transactions to SQL)
- SQL to Airtable summary: ~5 seconds (last 90 days)
- Subsequent syncs: ~2-5 seconds (only new transactions)
- Recommended: Daily (automated)

**Analytics Queries**:
- Airtable API: ~1-3 seconds per query (visual dashboard data)
- SQL Database: <10ms per query (historical analysis)
- Combined insights: Best of both worlds

---

## Security & Privacy

**Airtable Security**:
- API keys stored in `.env` file (gitignored)
- Personal Access Tokens expire and can be revoked
- Base-level permissions control access
- HTTPS enforced for all API calls

**Financial Data Security**:
- Full transaction history stays in local SQL database
- Only last 90 days synced to Airtable (for dashboard)
- Full account numbers NEVER stored (only last 4 digits)
- Plaid access tokens encrypted with Fernet (AES-128)
- Encryption keys stored with restrictive permissions (600)
- Sensitive data redacted from logs

**General Security**:
- All credentials stored in `.env` files (gitignored)
- OAuth tokens cached locally
- No credentials committed to git
- Session tokens auto-refresh
- SQL injection prevention via parameterized queries

---

## Benefits of Airtable vs Notion

### Airtable Advantages
- **Better relational database**: True foreign keys, rollups, lookups
- **More powerful formulas**: Richer formula language
- **Superior views**: More view types (Kanban, Calendar, Gallery, Timeline, Gantt)
- **Better automation**: Native automation builder
- **API consistency**: More reliable API with better documentation
- **Interfaces**: Build custom dashboards without code
- **Collaboration**: Better real-time collaboration features

### Notion Advantages
- **Unlimited pages**: No record limits (Airtable has 100k/base limit)
- **Rich text editing**: Better for documentation and notes
- **Nested pages**: Hierarchical organization
- **Templates**: Page templates for repeated structures

### Hybrid Strategy (Airtable + SQL)
- **Airtable**: Recent data (90 days) for visual dashboards and daily management
- **SQL**: Unlimited historical data for long-term analytics
- **Best of both worlds**: Visual interfaces + unlimited storage + fast analytics

---

**Built with Claude Code**

This structure is designed to be independently functional and can be used standalone or integrated with the existing SQL database for comprehensive life management with AI assistance.
