#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import Airtable from 'airtable';

// Environment variables
const AIRTABLE_API_KEY = process.env.AIRTABLE_ACCESS_TOKEN;
const AIRTABLE_BASE_ID = process.env.AIRTABLE_BASE_ID;

if (!AIRTABLE_API_KEY || !AIRTABLE_BASE_ID) {
  throw new Error('AIRTABLE_ACCESS_TOKEN and AIRTABLE_BASE_ID must be set');
}

// Initialize Airtable
const base = new Airtable({ apiKey: AIRTABLE_API_KEY }).base(AIRTABLE_BASE_ID);

// Table names from your .env
const TABLES = {
  DAY: 'Day',
  WEEK: 'Week',
  CALENDAR_EVENTS: 'Calendar Events',
  TASKS: 'Tasks',
  PROJECTS: 'Projects',
  CLASSES: 'Classes',
  TRAINING_PLANS: 'Training Plans',
  TRAINING_SESSIONS: 'Training Sessions',
  HEALTH_METRICS: 'Health Metrics',
  BODY_METRICS: 'Body Metrics',
  PLANNED_MEALS: 'Planned Meals',
  MEAL_PLANS: 'Meal Plans',
  RECIPES: 'Recipes',
  GROCERY_ITEMS: 'Grocery Items',
  WEEKLY_REVIEWS: 'Weekly Reviews',
};

// Helper function to get today's date in YYYY-MM-DD format
function getTodayDate(): string {
  const today = new Date();
  return today.toISOString().split('T')[0];
}

// Helper function to get date range for week
function getWeekDates(weekOffset: number = 0): { start: string; end: string } {
  const today = new Date();
  const dayOfWeek = today.getDay();
  const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // Adjust to Monday

  const monday = new Date(today.setDate(diff + (weekOffset * 7)));
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);

  return {
    start: monday.toISOString().split('T')[0],
    end: sunday.toISOString().split('T')[0],
  };
}

// Helper function to format records for display
function formatRecords(records: readonly any[], fields: string[] | null = null): string {
  if (records.length === 0) {
    return 'No records found.';
  }

  return Array.from(records).map(record => {
    const data = record.fields;
    if (fields) {
      const filtered: any = {};
      fields.forEach(field => {
        if (data[field] !== undefined) {
          filtered[field] = data[field];
        }
      });
      return JSON.stringify(filtered, null, 2);
    }
    return JSON.stringify(data, null, 2);
  }).join('\n---\n');
}

// Helper function to get Day record ID from date
async function getDayRecordId(dateStr: string): Promise<string | null> {
  try {
    const records = await base(TABLES.DAY)
      .select({
        filterByFormula: `{Day} = '${dateStr}'`,
        maxRecords: 1,
      })
      .all();

    if (records.length > 0) {
      return records[0].id;
    }
    return null;
  } catch (error) {
    console.error(`Error finding Day record for ${dateStr}:`, error);
    return null;
  }
}

// Helper function to get all Day record IDs for a date range
async function getDayRecordIdsForRange(startDate: string, endDate: string): Promise<string[]> {
  try {
    const records = await base(TABLES.DAY)
      .select({
        filterByFormula: `AND({Day} >= '${startDate}', {Day} <= '${endDate}')`,
      })
      .all();

    return records.map(r => r.id);
  } catch (error) {
    console.error(`Error finding Day records for range ${startDate} to ${endDate}:`, error);
    return [];
  }
}

// Helper function to group records by date
function groupByDate(records: any[], dateField: string): Record<string, any[]> {
  const grouped: Record<string, any[]> = {};

  records.forEach(record => {
    const date = record[dateField];
    if (date) {
      const dateKey = typeof date === 'string' ? date.split('T')[0] : date;
      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }
      grouped[dateKey].push(record);
    }
  });

  return grouped;
}

// Create the MCP server
const server = new Server(
  {
    name: 'airtable-planning',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define available tools
const tools: Tool[] = [
  {
    name: 'get_today_overview',
    description: 'Get an overview of today including calendar events, tasks, training, meals, and health metrics',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'get_week_overview',
    description: 'Get an overview of the current week including all planned activities',
    inputSchema: {
      type: 'object',
      properties: {
        week_offset: {
          type: 'number',
          description: 'Number of weeks from current week (0 = current, 1 = next, -1 = last)',
          default: 0,
        },
      },
    },
  },
  {
    name: 'get_complete_schedule',
    description: 'Get a complete schedule for a specific date or date range with all data in one call',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: {
          type: 'string',
          description: 'Start date in YYYY-MM-DD format (defaults to today)',
        },
        end_date: {
          type: 'string',
          description: 'End date in YYYY-MM-DD format (defaults to start_date)',
        },
      },
    },
  },
  {
    name: 'get_calendar_events',
    description: 'Get calendar events for a specific date range',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: {
          type: 'string',
          description: 'Start date in YYYY-MM-DD format (defaults to today)',
        },
        end_date: {
          type: 'string',
          description: 'End date in YYYY-MM-DD format (defaults to today)',
        },
      },
    },
  },
  {
    name: 'get_tasks',
    description: 'Get all tasks from the Tasks table',
    inputSchema: {
      type: 'object',
      properties: {
        limit: {
          type: 'number',
          description: 'Maximum number of tasks to return (default: 100)',
          default: 100,
        },
      },
    },
  },
  {
    name: 'get_training_sessions',
    description: 'Get training sessions for a date range',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: {
          type: 'string',
          description: 'Start date in YYYY-MM-DD format (defaults to today)',
        },
        end_date: {
          type: 'string',
          description: 'End date in YYYY-MM-DD format (defaults to 7 days from start)',
        },
      },
    },
  },
  {
    name: 'get_training_plans',
    description: 'Get training plans for a date range',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: {
          type: 'string',
          description: 'Start date in YYYY-MM-DD format (defaults to today)',
        },
        end_date: {
          type: 'string',
          description: 'End date in YYYY-MM-DD format (defaults to 7 days from start)',
        },
      },
    },
  },
  {
    name: 'get_health_metrics',
    description: 'Get health metrics (sleep, steps, heart rate, etc.) for a date range',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: {
          type: 'string',
          description: 'Start date in YYYY-MM-DD format (defaults to today)',
        },
        end_date: {
          type: 'string',
          description: 'End date in YYYY-MM-DD format (defaults to today)',
        },
      },
    },
  },
  {
    name: 'get_planned_meals',
    description: 'Get planned meals for a date range',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: {
          type: 'string',
          description: 'Start date in YYYY-MM-DD format (defaults to today)',
        },
        end_date: {
          type: 'string',
          description: 'End date in YYYY-MM-DD format (defaults to 7 days from start)',
        },
      },
    },
  },
  {
    name: 'get_recipes',
    description: 'Search for recipes by name',
    inputSchema: {
      type: 'object',
      properties: {
        search: {
          type: 'string',
          description: 'Search term for recipe name',
        },
        limit: {
          type: 'number',
          description: 'Maximum number of recipes to return (default: 20)',
          default: 20,
        },
      },
    },
  },
  {
    name: 'get_projects',
    description: 'Get all projects and their details',
    inputSchema: {
      type: 'object',
      properties: {
        limit: {
          type: 'number',
          description: 'Maximum number of projects to return (default: 100)',
          default: 100,
        },
      },
    },
  },
  {
    name: 'get_classes',
    description: 'Get class information and schedules',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
];

// Handle list tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'get_today_overview': {
        const today = getTodayDate();
        const dayRecordId = await getDayRecordId(today);

        const results: any = {
          date: today,
          day_record_id: dayRecordId,
          calendar_events: [],
          tasks: [],
          training_plans: [],
          training_sessions: [],
          meals: [],
          health: {},
        };

        // Get calendar events for today
        try {
          const events = await base(TABLES.CALENDAR_EVENTS)
            .select({
              filterByFormula: `{Date} = '${today}'`,
              sort: [{ field: 'Start Time', direction: 'asc' }],
            })
            .all();
          results.calendar_events = events.map(r => r.fields);
        } catch (error) {
          results.calendar_events_error = String(error);
        }

        // Get all tasks (Tasks table has no fields currently, so just return empty)
        try {
          const tasks = await base(TABLES.TASKS)
            .select({
              maxRecords: 50,
            })
            .all();
          results.tasks = tasks.map(r => r.fields);
        } catch (error) {
          results.tasks_error = String(error);
        }

        // Get training plans linked to today
        if (dayRecordId) {
          try {
            const plans = await base(TABLES.TRAINING_PLANS)
              .select({
                filterByFormula: `SEARCH('${dayRecordId}', ARRAYJOIN({Day}))`,
              })
              .all();
            results.training_plans = plans.map(r => r.fields);
          } catch (error) {
            results.training_plans_error = String(error);
          }

          // Get training sessions linked to today
          try {
            const sessions = await base(TABLES.TRAINING_SESSIONS)
              .select({
                filterByFormula: `SEARCH('${dayRecordId}', ARRAYJOIN({Day}))`,
              })
              .all();
            results.training_sessions = sessions.map(r => r.fields);
          } catch (error) {
            results.training_sessions_error = String(error);
          }
        }

        // Get planned meals for today
        try {
          const meals = await base(TABLES.PLANNED_MEALS)
            .select({
              filterByFormula: `{Date} = '${today}'`,
            })
            .all();
          results.meals = meals.map(r => r.fields);
        } catch (error) {
          results.meals_error = String(error);
        }

        // Get health metrics for today
        try {
          const health = await base(TABLES.HEALTH_METRICS)
            .select({
              filterByFormula: `{Name} = '${today}'`,
              maxRecords: 1,
            })
            .all();
          results.health = health.length > 0 ? health[0].fields : {};
        } catch (error) {
          results.health_error = String(error);
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      case 'get_week_overview': {
        const weekOffset = (args as any)?.week_offset ?? 0;
        const { start, end } = getWeekDates(weekOffset);

        const results: any = {
          week_start: start,
          week_end: end,
          days: {},
          summary: {
            total_events: 0,
            total_tasks: 0,
            total_training_plans: 0,
            total_training_sessions: 0,
            total_meals: 0,
          },
        };

        // Get all Day records for the week
        const dayRecordIds = await getDayRecordIdsForRange(start, end);

        // Get calendar events for the week
        try {
          const events = await base(TABLES.CALENDAR_EVENTS)
            .select({
              filterByFormula: `AND({Date} >= '${start}', {Date} <= '${end}')`,
              sort: [{ field: 'Date', direction: 'asc' }, { field: 'Start Time', direction: 'asc' }],
            })
            .all();

          const eventsByDate = groupByDate(events.map(r => r.fields), 'Date');
          Object.entries(eventsByDate).forEach(([date, evts]) => {
            if (!results.days[date]) results.days[date] = {};
            results.days[date].calendar_events = evts;
            results.summary.total_events += evts.length;
          });
        } catch (error) {
          results.calendar_events_error = String(error);
        }

        // Get all tasks
        try {
          const tasks = await base(TABLES.TASKS)
            .select({
              maxRecords: 100,
            })
            .all();
          results.tasks = tasks.map(r => r.fields);
          results.summary.total_tasks = tasks.length;
        } catch (error) {
          results.tasks_error = String(error);
        }

        // Get training plans for the week
        if (dayRecordIds.length > 0) {
          try {
            const dayIdFilter = dayRecordIds.map(id => `SEARCH('${id}', ARRAYJOIN({Day}))`).join(', ');
            const plans = await base(TABLES.TRAINING_PLANS)
              .select({
                filterByFormula: `OR(${dayIdFilter})`,
              })
              .all();

            results.training_plans = plans.map(r => r.fields);
            results.summary.total_training_plans = plans.length;
          } catch (error) {
            results.training_plans_error = String(error);
          }

          // Get training sessions for the week
          try {
            const dayIdFilter = dayRecordIds.map(id => `SEARCH('${id}', ARRAYJOIN({Day}))`).join(', ');
            const sessions = await base(TABLES.TRAINING_SESSIONS)
              .select({
                filterByFormula: `OR(${dayIdFilter})`,
              })
              .all();

            results.training_sessions = sessions.map(r => r.fields);
            results.summary.total_training_sessions = sessions.length;
          } catch (error) {
            results.training_sessions_error = String(error);
          }
        }

        // Get meals for the week
        try {
          const meals = await base(TABLES.PLANNED_MEALS)
            .select({
              filterByFormula: `AND({Date} >= '${start}', {Date} <= '${end}')`,
              sort: [{ field: 'Date', direction: 'asc' }],
            })
            .all();

          const mealsByDate = groupByDate(meals.map(r => r.fields), 'Date');
          Object.entries(mealsByDate).forEach(([date, mls]) => {
            if (!results.days[date]) results.days[date] = {};
            results.days[date].planned_meals = mls;
            results.summary.total_meals += mls.length;
          });
        } catch (error) {
          results.meals_error = String(error);
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      case 'get_complete_schedule': {
        const startDate = (args as any)?.start_date ?? getTodayDate();
        const endDate = (args as any)?.end_date ?? startDate;

        const results: any = {
          date_range: {
            start: startDate,
            end: endDate,
          },
          days: [],
        };

        // Get Day record IDs for the range
        const dayRecords = await base(TABLES.DAY)
          .select({
            filterByFormula: `AND({Day} >= '${startDate}', {Day} <= '${endDate}')`,
            sort: [{ field: 'Day', direction: 'asc' }],
          })
          .all();

        // For each day, gather all data
        for (const dayRecord of dayRecords) {
          const dayId = dayRecord.id;
          const date = dayRecord.fields.Day as string;

          const dayData: any = {
            date,
            weekday: dayRecord.fields.Weekday,
            calendar_events: [],
            training_plans: [],
            training_sessions: [],
            meals: [],
            health_metrics: null,
          };

          // Calendar events
          try {
            const events = await base(TABLES.CALENDAR_EVENTS)
              .select({
                filterByFormula: `{Date} = '${date}'`,
                sort: [{ field: 'Start Time', direction: 'asc' }],
              })
              .all();
            dayData.calendar_events = events.map(r => r.fields);
          } catch (error) {
            dayData.calendar_events_error = String(error);
          }

          // Training plans
          try {
            const plans = await base(TABLES.TRAINING_PLANS)
              .select({
                filterByFormula: `SEARCH('${dayId}', ARRAYJOIN({Day}))`,
              })
              .all();
            dayData.training_plans = plans.map(r => r.fields);
          } catch (error) {
            dayData.training_plans_error = String(error);
          }

          // Training sessions
          try {
            const sessions = await base(TABLES.TRAINING_SESSIONS)
              .select({
                filterByFormula: `SEARCH('${dayId}', ARRAYJOIN({Day}))`,
              })
              .all();
            dayData.training_sessions = sessions.map(r => r.fields);
          } catch (error) {
            dayData.training_sessions_error = String(error);
          }

          // Meals
          try {
            const meals = await base(TABLES.PLANNED_MEALS)
              .select({
                filterByFormula: `{Date} = '${date}'`,
              })
              .all();
            dayData.meals = meals.map(r => r.fields);
          } catch (error) {
            dayData.meals_error = String(error);
          }

          // Health metrics
          try {
            const health = await base(TABLES.HEALTH_METRICS)
              .select({
                filterByFormula: `{Name} = '${date}'`,
                maxRecords: 1,
              })
              .all();
            dayData.health_metrics = health.length > 0 ? health[0].fields : null;
          } catch (error) {
            dayData.health_metrics_error = String(error);
          }

          results.days.push(dayData);
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      case 'get_calendar_events': {
        const startDate = (args as any)?.start_date ?? getTodayDate();
        const endDate = (args as any)?.end_date ?? startDate;

        const records = await base(TABLES.CALENDAR_EVENTS)
          .select({
            filterByFormula: `AND({Date} >= '${startDate}', {Date} <= '${endDate}')`,
            sort: [{ field: 'Date', direction: 'asc' }, { field: 'Start Time', direction: 'asc' }],
          })
          .all();

        return {
          content: [
            {
              type: 'text',
              text: formatRecords(records),
            },
          ],
        };
      }

      case 'get_tasks': {
        const limit = (args as any)?.limit ?? 100;

        const records = await base(TABLES.TASKS)
          .select({
            maxRecords: limit,
          })
          .all();

        return {
          content: [
            {
              type: 'text',
              text: formatRecords(records),
            },
          ],
        };
      }

      case 'get_training_sessions': {
        const startDate = (args as any)?.start_date ?? getTodayDate();
        const endDateDefault = new Date(startDate);
        endDateDefault.setDate(endDateDefault.getDate() + 7);
        const endDate = (args as any)?.end_date ?? endDateDefault.toISOString().split('T')[0];

        // Get Day record IDs for the range
        const dayRecordIds = await getDayRecordIdsForRange(startDate, endDate);

        if (dayRecordIds.length === 0) {
          return {
            content: [
              {
                type: 'text',
                text: 'No Day records found for this date range.',
              },
            ],
          };
        }

        const dayIdFilter = dayRecordIds.map(id => `SEARCH('${id}', ARRAYJOIN({Day}))`).join(', ');
        const records = await base(TABLES.TRAINING_SESSIONS)
          .select({
            filterByFormula: `OR(${dayIdFilter})`,
          })
          .all();

        return {
          content: [
            {
              type: 'text',
              text: formatRecords(records),
            },
          ],
        };
      }

      case 'get_training_plans': {
        const startDate = (args as any)?.start_date ?? getTodayDate();
        const endDateDefault = new Date(startDate);
        endDateDefault.setDate(endDateDefault.getDate() + 7);
        const endDate = (args as any)?.end_date ?? endDateDefault.toISOString().split('T')[0];

        // Get Day record IDs for the range
        const dayRecordIds = await getDayRecordIdsForRange(startDate, endDate);

        if (dayRecordIds.length === 0) {
          return {
            content: [
              {
                type: 'text',
                text: 'No Day records found for this date range.',
              },
            ],
          };
        }

        const dayIdFilter = dayRecordIds.map(id => `SEARCH('${id}', ARRAYJOIN({Day}))`).join(', ');
        const records = await base(TABLES.TRAINING_PLANS)
          .select({
            filterByFormula: `OR(${dayIdFilter})`,
          })
          .all();

        return {
          content: [
            {
              type: 'text',
              text: formatRecords(records),
            },
          ],
        };
      }

      case 'get_health_metrics': {
        const startDate = (args as any)?.start_date ?? getTodayDate();
        const endDate = (args as any)?.end_date ?? startDate;

        const records = await base(TABLES.HEALTH_METRICS)
          .select({
            filterByFormula: `AND({Name} >= '${startDate}', {Name} <= '${endDate}')`,
            sort: [{ field: 'Name', direction: 'asc' }],
          })
          .all();

        return {
          content: [
            {
              type: 'text',
              text: formatRecords(records),
            },
          ],
        };
      }

      case 'get_planned_meals': {
        const startDate = (args as any)?.start_date ?? getTodayDate();
        const endDateDefault = new Date(startDate);
        endDateDefault.setDate(endDateDefault.getDate() + 7);
        const endDate = (args as any)?.end_date ?? endDateDefault.toISOString().split('T')[0];

        const records = await base(TABLES.PLANNED_MEALS)
          .select({
            filterByFormula: `AND({Date} >= '${startDate}', {Date} <= '${endDate}')`,
            sort: [{ field: 'Date', direction: 'asc' }],
          })
          .all();

        return {
          content: [
            {
              type: 'text',
              text: formatRecords(records),
            },
          ],
        };
      }

      case 'get_recipes': {
        const search = (args as any)?.search;
        const limit = (args as any)?.limit ?? 20;

        let formula = '';
        if (search) {
          formula = `FIND(LOWER('${search}'), LOWER({Name}))`;
        }

        const selectOptions: any = {
          maxRecords: limit,
        };
        if (formula) {
          selectOptions.filterByFormula = formula;
        }

        const records = await base(TABLES.RECIPES).select(selectOptions).all();

        return {
          content: [
            {
              type: 'text',
              text: formatRecords(records),
            },
          ],
        };
      }

      case 'get_projects': {
        const limit = (args as any)?.limit ?? 100;

        const records = await base(TABLES.PROJECTS)
          .select({
            maxRecords: limit,
          })
          .all();

        return {
          content: [
            {
              type: 'text',
              text: formatRecords(records),
            },
          ],
        };
      }

      case 'get_classes': {
        const records = await base(TABLES.CLASSES).select().all();

        return {
          content: [
            {
              type: 'text',
              text: formatRecords(records),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Airtable Planning MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
