# Airtable MCP Server - Quick Reference

**Version:** 1.0.0 | **Updated:** January 21, 2026

## 🚀 Quick Start

### Common Queries

Just ask Claude naturally:

```
What's my schedule for today?
Show me my week overview
What training do I have planned this week?
What meals should I prep for next week?
How did I sleep last week?
Find a high-protein recipe
What are my upcoming class projects?
```

---

## 📋 All Functions at a Glance

| Function | Purpose | Key Parameters |
|----------|---------|----------------|
| **get_today_overview** | Everything for today | None |
| **get_week_overview** | Weekly summary | week_offset (0=current) |
| **get_complete_schedule** ⭐ | Unified data retrieval | start_date, end_date |
| **get_calendar_events** | Calendar events | start_date, end_date |
| **get_tasks** | All tasks | limit (default: 100) |
| **get_training_sessions** | Completed workouts | start_date, end_date |
| **get_training_plans** | Planned workouts | start_date, end_date |
| **get_health_metrics** | Health data | start_date, end_date |
| **get_planned_meals** | Meal schedule | start_date, end_date |
| **get_recipes** | Recipe search | search, limit |
| **get_projects** | Academic projects | limit |
| **get_classes** | Course info | None |

⭐ = Most powerful/recommended function

---

## 🎯 Best Functions for Common Tasks

### Daily Planning
→ **get_today_overview** or **get_complete_schedule**

### Weekly Planning
→ **get_week_overview** or **get_complete_schedule** (with date range)

### Training Tracking
→ **get_training_sessions** (completed) + **get_training_plans** (planned)

### Meal Planning
→ **get_planned_meals** + **get_recipes**

### Health Monitoring
→ **get_health_metrics**

---

## 📅 Date Format

**Always use:** `YYYY-MM-DD`

**Examples:**
- ✅ `2026-01-21`
- ❌ `01/21/2026`
- ❌ `21-01-2026`

---

## 🔑 Critical Field Names

### Calendar Events
- `Date` - YYYY-MM-DD
- `Start Time` - ISO datetime
- `Name`, `Title`, `Location`

### Training Plans
- `Day` - Linked to Day table
- `Workout Type`, `Status`
- `Workout Description`

### Training Sessions
- `Day` - Linked to Day table
- `Activity Type`
- `Start Time`, `Moving Duration (min)`

### Health Metrics
- `Name` - YYYY-MM-DD (primary field)
- `Steps`, `Sleep Score`, `Resting HR`

### Planned Meals
- `Date` - YYYY-MM-DD
- `Meal Type`, `Recipe`, `Status`

---

## 💡 Pro Tips

1. **Use get_complete_schedule for comprehensive views**
   - Single call, all data
   - Best for detailed daily/weekly planning

2. **Week offset for week_overview**
   - 0 = current week
   - 1 = next week
   - -1 = last week

3. **Training data filters via Day records**
   - Training Plans and Sessions link to Day table
   - Server handles the complexity automatically

4. **Empty results are normal**
   - Tasks table currently has no fields
   - Some dates may have no events/meals
   - Not an error if "No records found"

5. **Date ranges are inclusive**
   - start_date and end_date both included
   - Monday to Sunday for full week

---

## ⚠️ Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| "Unknown field name" | Check AIRTABLE_FIELD_MAPPING.md |
| Empty results | Verify date format (YYYY-MM-DD) |
| "No Day records" | Day table needs records for that date |
| Server not responding | Check .env credentials |
| Slow responses | Large date ranges - use smaller ranges |

---

## 📚 Documentation Files

- **AIRTABLE_MCP_DOCUMENTATION.md** - Complete guide (500+ lines)
- **test_mcp_functions.md** - Test suite with examples
- **AIRTABLE_SCHEMA.md** - Full table schemas
- **AIRTABLE_FIELD_MAPPING.md** - Field name reference
- **UPDATE_SUMMARY.md** - What changed in this update
- **VERIFICATION_CHECKLIST.md** - Testing checklist
- **QUICK_REFERENCE.md** - This file

---

## 🔧 Technical Quick Ref

### Environment Setup
```bash
# .env file must contain:
AIRTABLE_ACCESS_TOKEN=your_token
AIRTABLE_BASE_ID=appKYFUTDs7tDg4Wr
```

### Build Server
```bash
cd airtable-mcp-server
npm run build
```

### Inspect Schema
```bash
node inspect_airtable_schema.js
```

---

## 📊 Data Structure Overview

```
Day Table (Primary)
├── Date: YYYY-MM-DD
├── Weekday: String
└── Links to:
    ├── Calendar Events
    ├── Training Plans
    ├── Training Sessions
    ├── Planned Meals
    └── Health Metrics

Week Table
├── Name: W-YY format
├── Start/End Date
└── Links to 7 Day records
```

---

## 🎓 Example Queries

### Get today's complete schedule
```
What's my schedule for today?
```
*Uses: get_today_overview*

### Plan next week
```
Show me my week overview for next week
```
*Uses: get_week_overview with week_offset: 1*

### Review training
```
What training did I complete last week?
```
*Uses: get_training_sessions with date range*

### Meal prep planning
```
What meals do I need to prep this week?
```
*Uses: get_planned_meals*

### Find recipes
```
Find recipes with chicken
```
*Uses: get_recipes with search: "chicken"*

### Check sleep quality
```
How did I sleep this week?
```
*Uses: get_health_metrics with Sleep Score field*

### View class projects
```
What projects are due this month?
```
*Uses: get_projects*

---

## ✨ New Features in v1.0.0

✅ Fixed all field name issues
✅ Added get_complete_schedule (unified data)
✅ Added get_training_plans
✅ Improved week overview (grouping + summary)
✅ Better error handling
✅ Comprehensive documentation

---

## 🆘 Need Help?

1. Check **AIRTABLE_MCP_DOCUMENTATION.md** for detailed info
2. Review **test_mcp_functions.md** for examples
3. Verify field names in **AIRTABLE_FIELD_MAPPING.md**
4. Run verification tests in **VERIFICATION_CHECKLIST.md**

---

**Remember:** The MCP server is designed to understand natural language queries. Just ask what you need in plain English!

**Example:** Instead of memorizing function names, just say:
- "What's happening this week?"
- "Show me my training schedule"
- "What should I eat tomorrow?"

Claude will automatically use the right functions! 🎉
