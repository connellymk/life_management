# Airtable Planning MCP Server

This MCP (Model Context Protocol) server provides Claude Chat with read access to your Airtable personal planning system.

## Installation

The server has been installed and configured at:
```
C:\Users\Administrator\Desktop\personal_assistant\airtable-mcp-server
```

## Configuration

Claude Desktop has been configured to use this server at:
```
C:\Users\Administrator\AppData\Roaming\Claude\claude_desktop_config.json
```

The server connects to your Airtable base using:
- **Base ID**: `appKYFUTDs7tDg4Wr`
- **API Token**: Configured in environment variables

## Available Tools

Once Claude Desktop is restarted, you'll have access to these tools:

### Daily & Weekly Planning
- **get_today_overview** - Complete overview of today (calendar, tasks, training, meals, health)
- **get_week_overview** - Complete overview of the current week (or specify offset for other weeks)

### Calendar
- **get_calendar_events** - Get calendar events for a specific date range

### Tasks & Projects
- **get_tasks** - Get tasks (filter by status, due date, or show/hide completed)
- **get_projects** - Get all projects (filter by status)
- **get_classes** - Get class information and schedules

### Training & Health
- **get_training_plans** - Get training plans and sessions for a date range
- **get_health_metrics** - Get health metrics (sleep, steps, heart rate, etc.)

### Meal Planning
- **get_planned_meals** - Get planned meals for a date range
- **get_recipes** - Search for recipes by name or ingredient

## Usage Examples

Once you restart Claude Desktop, you can use natural language like:

```
"What's on my schedule today?"
"Show me this week's overview"
"What tasks do I have due this week?"
"What's my training plan for the next 7 days?"
"How did I sleep last night?"
"What recipes do we have for chicken?"
"What meals are planned for this week?"
```

## How to Restart Claude Desktop

1. **Completely quit Claude Desktop** (not just close the window - use File > Exit or the system tray)
2. **Wait a few seconds**
3. **Reopen Claude Desktop**
4. **Test the connection** by asking: "What MCP tools do you have available?"

You should see all the tools listed above.

## Troubleshooting

If the server doesn't work:

1. **Check the build** - Make sure the server built successfully:
   ```bash
   cd C:\Users\Administrator\Desktop\personal_assistant\airtable-mcp-server
   npm run build
   ```

2. **Check the config** - Verify the config file exists and is correct:
   ```bash
   cat C:\Users\Administrator\AppData\Roaming\Claude\claude_desktop_config.json
   ```

3. **Check Claude Desktop logs** - Look for errors in:
   ```
   C:\Users\Administrator\AppData\Roaming\Claude\logs
   ```

4. **Verify Airtable credentials** - Make sure your API token has the right scopes:
   - `data.records:read`
   - `data.records:write` (not used yet, but good to have)
   - `schema.bases:read`

## Making Changes

If you need to modify the server:

1. Edit files in `src/`
2. Rebuild: `npm run build`
3. Restart Claude Desktop

## Data Access

This server provides **read-only** access to your Airtable data. It queries these tables:

- Day
- Week
- Calendar Events
- Tasks
- Projects
- Classes
- Training Plans
- Training Sessions
- Health Metrics
- Body Metrics
- Planned Meals
- Meal Plans
- Recipes
- Grocery Items
- Weekly Reviews

## Future Enhancements

Possible additions (not yet implemented):
- Write capabilities (create tasks, add calendar events, etc.)
- Update capabilities (mark tasks complete, reschedule events, etc.)
- Delete capabilities (with appropriate safeguards)
- Weekly review creation
- Goal tracking
- Budget and finance tracking
