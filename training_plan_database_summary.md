# Training Plan Database - Structure Summary

## Database Information
**Database Name:** Training Plan - Beaverhead 100k  
**Database ID:** 9a3c2dd1b2354f2a8e8f330d7fda16c3  
**Data Source ID:** 24620dff-0071-4fee-a445-03a56ed60843  
**Race Date:** July 11, 2026  
**Training Duration:** 25 weeks (January 20 - July 11, 2026)

---

## Complete Field List

### Core Identification
1. **Name** (Title field) - Workout name/identifier
2. **Date** (Date) - Scheduled workout date
3. **Week Number** (Number) - Training week 1-25
4. **Day of Week** (Select) - Monday through Sunday

### Training Structure
5. **Training Phase** (Select)
   - Base Building (green)
   - Build 1 (blue)
   - Build 2 (purple)
   - Peak (red)
   - Taper (orange)

6. **Workout Type** (Select)
   - Long Run (red)
   - Easy Run (green)
   - Tempo Run (orange)
   - Hill Workout (brown)
   - Intervals (purple)
   - Recovery Run (blue)
   - Strength Training (yellow)
   - Cross Training (gray)
   - Rest Day (default)

### Planned Workout Details
7. **Planned Distance** (Number with commas) - Miles
8. **Planned Duration** (Number) - Minutes
9. **Planned Elevation Gain** (Number with commas) - Feet
10. **Target Pace Effort** (Text) - Pace or effort zone description
11. **Workout Description** (Rich Text) - Detailed instructions

### Tracking & Status
12. **Status** (Select)
    - Planned (gray)
    - Completed (green)
    - Skipped (yellow)
    - Modified (blue)
    - Missed (red)

13. **Priority** (Select)
    - Key Workout (red)
    - Important (orange)
    - Standard (blue)
    - Optional (gray)

14. **Workout Notes** (Rich Text) - Post-workout reflections

### Focus & Goals
15. **Focus Areas** (Multi-select)
    - Endurance (blue)
    - Speed (red)
    - Hills (brown)
    - Recovery (green)
    - Nutrition Practice (orange)
    - Gear Testing (purple)
    - Mental Training (pink)

16. **Weekly Mileage Target** (Number with commas) - Miles
17. **Weekly Elevation Target** (Number with commas) - Feet

### Database Relations
18. **Completed Workout** (Relation) → Links to Completed Workouts database
    - Database ID: 2e990d86c150801d8873c4e34f5a142d
    - Data Source: 2e990d86-c150-801c-a504-000b29c6bdf0

19. **Calendar Event** (Relation) → Links to Calendar Events database
    - Database ID: 2e890d86c150802fa4a6efb3c7bdd4b5
    - Data Source: 2e890d86-c150-801e-87d3-000b40a2b7f7

20. **Daily Metrics** (Relation) → Links to Daily Metrics database
    - Database ID: 2e990d86c15080c8a201e5c06c69499f
    - Data Source: 2e990d86-c150-800c-9143-000b8bd2dbed

---

## Training Phase Breakdown

### Base Building (Weeks 1-8): January 20 - March 15
- Focus on aerobic endurance
- Gradual mileage building
- Long runs: 12-18 miles
- Establish consistent training habit

### Build 1 (Weeks 9-14): March 16 - April 26
- Increase weekly volume
- Add more elevation/vertical gain
- Long runs: 18-24 miles
- Introduce back-to-back long runs

### Build 2 (Weeks 15-20): April 27 - June 7
- Peak mileage weeks
- Long runs: 24-32 miles
- Simulate race conditions
- Practice nutrition and gear

### Peak (Weeks 21-22): June 8 - June 21
- Highest volume weeks
- Include 50k training run or similar distance
- Final major training push

### Taper (Weeks 23-25): June 22 - July 11
- Reduce volume significantly
- Maintain intensity briefly
- Focus on rest and recovery
- **Race Day: July 11, 2026**

---

## Recommended Database Views

### 1. Calendar View
- Group by: Week Number
- Display: Date, Workout Type, Planned Distance
- Filter: Show current and upcoming weeks

### 2. Training Phase Board
- Group by: Training Phase
- Display: Name, Date, Status, Priority
- Shows progression through training phases

### 3. Weekly Summary Table
- Group by: Week Number
- Display: All planned workouts
- Calculate: Total weekly mileage and elevation
- Filter: By Training Phase

### 4. Key Workouts Only
- Filter: Priority = "Key Workout"
- Sort: By Date
- Display: Name, Date, Workout Type, Status

### 5. Completed vs Planned
- Filter: Status in ["Completed", "Modified", "Missed"]
- Group by: Week Number
- Shows actual training completion

---

## Future Enhancement: Join Table Strategy

As you mentioned, creating a separate "Daily Training Summary" join table would provide a cleaner relational structure. This table would:

**Proposed Join Table Structure:**
- **Date** (Primary key)
- **Training Plan Workout** (Relation)
- **Completed Workout** (Relation)
- **Calendar Events** (Relation - multiple)
- **Daily Metrics** (Relation)
- **Nutrition Log** (Relation - future)
- **Hydration Log** (Relation - future)

**Benefits:**
1. Single source of truth for each date
2. Easier querying across all data sources
3. Better for analytics and reporting
4. Cleaner data architecture
5. Easier to add new data types (nutrition, sleep quality, etc.)

---

## Next Steps

1. **Populate Base Building Phase** - Create workout entries for weeks 1-8
2. **Establish Weekly Patterns** - Define typical week structure
3. **Set Mileage Progression** - Plan gradual weekly increases
4. **Identify Key Workouts** - Mark critical long runs and quality sessions
5. **Create Calendar Integration** - Sync planned workouts to calendar
6. **Consider Join Table** - Implement if managing complexity increases

---

## Database URL
https://www.notion.so/9a3c2dd1b2354f2a8e8f330d7fda16c3

