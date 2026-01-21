#!/usr/bin/env node

/**
 * Script to inspect Airtable base and document all table schemas
 * This will help us identify the correct field names for the MCP server
 */

const Airtable = require('./airtable-mcp-server/node_modules/airtable');
const fs = require('fs');
const path = require('path');

// Read .env file manually
function loadEnv() {
  try {
    const envPath = path.join(__dirname, '.env');
    const envContent = fs.readFileSync(envPath, 'utf8');
    const env = {};

    envContent.split('\n').forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key && valueParts.length > 0) {
          env[key.trim()] = valueParts.join('=').trim().replace(/^["']|["']$/g, '');
        }
      }
    });

    return env;
  } catch (error) {
    console.error('Error reading .env file:', error.message);
    return {};
  }
}

const env = loadEnv();

// Configuration
const AIRTABLE_API_KEY = env.AIRTABLE_ACCESS_TOKEN || process.env.AIRTABLE_ACCESS_TOKEN;
const AIRTABLE_BASE_ID = env.AIRTABLE_BASE_ID || process.env.AIRTABLE_BASE_ID;

if (!AIRTABLE_API_KEY || !AIRTABLE_BASE_ID) {
  console.error('ERROR: AIRTABLE_ACCESS_TOKEN and AIRTABLE_BASE_ID must be set in .env');
  process.exit(1);
}

const base = new Airtable({ apiKey: AIRTABLE_API_KEY }).base(AIRTABLE_BASE_ID);

// Tables to inspect
const TABLES = [
  'Day',
  'Week',
  'Calendar Events',
  'Tasks',
  'Projects',
  'Classes',
  'Training Plans',
  'Training Sessions',
  'Health Metrics',
  'Body Metrics',
  'Planned Meals',
  'Meal Plans',
  'Recipes',
  'Grocery Items',
  'Weekly Reviews',
];

/**
 * Get field information from a table by examining actual records
 */
async function inspectTable(tableName) {
  console.log(`\n${'='.repeat(70)}`);
  console.log(`Inspecting table: ${tableName}`);
  console.log('='.repeat(70));

  try {
    // Fetch first 5 records to see field structure
    const records = await base(tableName)
      .select({
        maxRecords: 5,
      })
      .all();

    if (records.length === 0) {
      console.log('⚠️  Table exists but has no records');
      return {
        tableName,
        exists: true,
        recordCount: 0,
        fields: [],
        sampleData: [],
      };
    }

    console.log(`✅ Found ${records.length} sample records`);

    // Collect all unique field names from the sample
    const fieldSet = new Set();
    records.forEach(record => {
      Object.keys(record.fields).forEach(field => fieldSet.add(field));
    });

    const fields = Array.from(fieldSet).sort();
    console.log(`\nFields found (${fields.length}):`);
    fields.forEach(field => {
      console.log(`  - ${field}`);
    });

    // Analyze field types from first record
    console.log(`\nField types (from first record):`);
    const firstRecord = records[0].fields;
    const fieldTypes = {};

    fields.forEach(field => {
      const value = firstRecord[field];
      let type = typeof value;

      if (Array.isArray(value)) {
        type = `array (${value.length} items)`;
        if (value.length > 0) {
          const firstItem = value[0];
          if (typeof firstItem === 'string' && firstItem.startsWith('rec')) {
            type += ' - likely linked records';
          } else {
            type += ` - first item type: ${typeof firstItem}`;
          }
        }
      } else if (value instanceof Date) {
        type = 'date';
      } else if (value === null || value === undefined) {
        type = 'null/undefined';
      } else if (typeof value === 'string') {
        // Check if it looks like a date
        if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
          type = 'string (date format)';
        } else if (value.startsWith('rec')) {
          type = 'string (record ID?)';
        }
      }

      fieldTypes[field] = type;
      console.log(`  - ${field}: ${type}`);
    });

    // Show sample data (first 2 records)
    console.log(`\nSample data (first 2 records):`);
    records.slice(0, 2).forEach((record, index) => {
      console.log(`\nRecord ${index + 1}:`);
      console.log(JSON.stringify(record.fields, null, 2));
    });

    return {
      tableName,
      exists: true,
      recordCount: records.length,
      fields,
      fieldTypes,
      sampleData: records.slice(0, 2).map(r => r.fields),
    };

  } catch (error) {
    if (error.statusCode === 404 || error.message.includes('Could not find table')) {
      console.log('❌ Table does not exist');
      return {
        tableName,
        exists: false,
        error: 'Table not found',
      };
    } else {
      console.log(`❌ Error: ${error.message}`);
      return {
        tableName,
        exists: false,
        error: error.message,
      };
    }
  }
}

/**
 * Generate markdown documentation
 */
function generateMarkdown(results) {
  let md = '# Airtable Schema Documentation\n\n';
  md += `**Generated:** ${new Date().toISOString()}\n\n`;
  md += `**Base ID:** ${AIRTABLE_BASE_ID}\n\n`;
  md += '---\n\n';

  results.forEach(result => {
    md += `## ${result.tableName}\n\n`;

    if (!result.exists) {
      md += `**Status:** ❌ Table does not exist\n\n`;
      md += `**Error:** ${result.error}\n\n`;
      return;
    }

    if (result.recordCount === 0) {
      md += `**Status:** ⚠️ Table exists but has no records\n\n`;
      return;
    }

    md += `**Status:** ✅ Active (${result.recordCount} sample records inspected)\n\n`;
    md += `### Fields\n\n`;
    md += `| Field Name | Type | Notes |\n`;
    md += `|------------|------|-------|\n`;

    result.fields.forEach(field => {
      const type = result.fieldTypes[field] || 'unknown';
      md += `| \`${field}\` | ${type} | |\n`;
    });

    md += `\n### Sample Data\n\n`;
    md += '```json\n';
    md += JSON.stringify(result.sampleData[0] || {}, null, 2);
    md += '\n```\n\n';
  });

  return md;
}

/**
 * Generate field mapping reference for the MCP server
 */
function generateFieldMapping(results) {
  let mapping = '# Field Name Reference for MCP Server\n\n';
  mapping += '## Quick Reference\n\n';
  mapping += 'Use these exact field names in filterByFormula and sort operations:\n\n';

  results.forEach(result => {
    if (!result.exists || result.recordCount === 0) return;

    mapping += `### ${result.tableName}\n\n`;
    mapping += '```typescript\n';
    mapping += `// Field names:\n`;
    result.fields.forEach(field => {
      const type = result.fieldTypes[field] || 'unknown';
      mapping += `"${field}" // ${type}\n`;
    });
    mapping += '```\n\n';
  });

  return mapping;
}

/**
 * Main execution
 */
async function main() {
  console.log('╔═══════════════════════════════════════════════════════════════════╗');
  console.log('║       Airtable Schema Inspector                                   ║');
  console.log('╚═══════════════════════════════════════════════════════════════════╝');
  console.log(`\nBase ID: ${AIRTABLE_BASE_ID}`);
  console.log(`Tables to inspect: ${TABLES.length}\n`);

  const results = [];

  for (const tableName of TABLES) {
    const result = await inspectTable(tableName);
    results.push(result);

    // Add small delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  // Generate documentation
  console.log('\n\n' + '='.repeat(70));
  console.log('GENERATING DOCUMENTATION');
  console.log('='.repeat(70));

  const markdown = generateMarkdown(results);
  const mappingDoc = generateFieldMapping(results);

  // Write to files
  const schemaFile = 'AIRTABLE_SCHEMA.md';
  const mappingFile = 'AIRTABLE_FIELD_MAPPING.md';

  fs.writeFileSync(schemaFile, markdown);
  console.log(`\n✅ Schema documentation written to: ${schemaFile}`);

  fs.writeFileSync(mappingFile, mappingDoc);
  console.log(`✅ Field mapping reference written to: ${mappingFile}`);

  // Summary
  console.log('\n\n' + '='.repeat(70));
  console.log('SUMMARY');
  console.log('='.repeat(70));

  const existingTables = results.filter(r => r.exists);
  const missingTables = results.filter(r => !r.exists);
  const emptyTables = results.filter(r => r.exists && r.recordCount === 0);
  const populatedTables = results.filter(r => r.exists && r.recordCount > 0);

  console.log(`\n✅ Existing tables: ${existingTables.length}/${TABLES.length}`);
  console.log(`   - Populated: ${populatedTables.length}`);
  console.log(`   - Empty: ${emptyTables.length}`);
  console.log(`❌ Missing tables: ${missingTables.length}`);

  if (missingTables.length > 0) {
    console.log('\nMissing tables:');
    missingTables.forEach(t => console.log(`   - ${t.tableName}`));
  }

  if (emptyTables.length > 0) {
    console.log('\nEmpty tables:');
    emptyTables.forEach(t => console.log(`   - ${t.tableName}`));
  }

  console.log('\n' + '='.repeat(70));
  console.log('INSPECTION COMPLETE');
  console.log('='.repeat(70));
}

// Run the script
main().catch(error => {
  console.error('\n❌ Fatal error:', error);
  process.exit(1);
});
