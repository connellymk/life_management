# Quick Start Guide

## ✅ Installation Complete!

Your Airtable MCP server has been successfully installed and configured.

## 🚀 Next Steps

### 1. Restart Claude Desktop

**IMPORTANT:** You must completely restart Claude Desktop for the changes to take effect.

1. Close all Claude Desktop windows
2. Find Claude Desktop in your system tray (bottom right of screen)
3. Right-click and select "Exit" or "Quit"
4. Wait 5 seconds
5. Open Claude Desktop again

### 2. Verify the Installation

Once Claude Desktop reopens, start a new conversation and type:

```
What MCP tools do you have available?
```

You should see a list of 10 tools including:
- get_today_overview
- get_week_overview
- get_calendar_events
- get_tasks
- get_training_plans
- get_health_metrics
- get_planned_meals
- get_recipes
- get_projects
- get_classes

### 3. Try It Out!

Here are some example questions you can ask:

**Daily Planning:**
```
What's on my schedule today?
What do I have going on today?
Show me today's overview
```

**Weekly Planning:**
```
What does my week look like?
Show me this week's schedule
What's coming up this week?
```

**Tasks:**
```
What tasks do I need to complete?
Show me my incomplete tasks
What's due this week?
```

**Training:**
```
What's my training plan for this week?
Do I have any workouts scheduled?
```

**Health:**
```
How did I sleep last night?
Show me my health metrics from yesterday
```

**Meals:**
```
What meals are planned for this week?
What recipes do we have for chicken?
What's for dinner tonight?
```

## 📊 What Data Can Claude See?

Claude can now see all your planning data from Airtable:

- ✅ Calendar Events
- ✅ Tasks & Projects
- ✅ Classes
- ✅ Training Plans & Sessions
- ✅ Health & Body Metrics
- ✅ Meal Plans & Recipes
- ✅ Grocery Items
- ✅ Weekly Reviews

## 🔒 Privacy & Security

- The MCP server runs **locally on your computer**
- Your data stays in Airtable - nothing is copied or stored elsewhere
- Claude Chat can **read** your data but cannot modify it (read-only access)
- Your Airtable credentials are stored securely in the config file

## 🐛 Troubleshooting

### Claude doesn't see the MCP tools

1. Make sure you **completely quit** Claude Desktop (not just closed windows)
2. Check that the config file exists:
   ```
   C:\Users\Administrator\AppData\Roaming\Claude\claude_desktop_config.json
   ```
3. Check Claude Desktop logs for errors:
   ```
   C:\Users\Administrator\AppData\Roaming\Claude\logs
   ```

### "Connection error" or "Server not responding"

1. Verify the server built successfully:
   ```bash
   cd C:\Users\Administrator\Desktop\personal_assistant\airtable-mcp-server
   npm run build
   ```
2. Check that Node.js is installed: `node --version`
3. Restart Claude Desktop again

### "Permission denied" or "Access denied"

1. Check your Airtable API token is valid
2. Verify the token has these scopes:
   - data.records:read
   - schema.bases:read
3. Make sure the Base ID is correct: `appKYFUTDs7tDg4Wr`

## 📝 Tips for Working with Claude

Once the MCP server is working, you can have natural conversations with Claude about your schedule:

**Good questions:**
- "Help me plan my day"
- "What should I prioritize this week?"
- "Am I free tomorrow afternoon?"
- "Do I have any conflicts this week?"
- "What's my workout schedule?"

**Claude can help you:**
- Identify scheduling conflicts
- Prioritize tasks based on due dates
- Plan your week strategically
- Track your progress on projects
- Analyze your health trends
- Plan meals for the week

## 🎉 You're All Set!

Just restart Claude Desktop and start planning with AI assistance!

If you have any issues, check the main README.md file for detailed troubleshooting steps.
