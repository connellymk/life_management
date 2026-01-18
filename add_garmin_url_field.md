# Add Garmin URL Field to Training Sessions Table

The Training Sessions table needs a "Garmin URL" field to store the direct link to each activity on Garmin Connect.

## Option 1: Add Manually in Airtable (Recommended)

1. Open your Airtable base
2. Go to the **Training Sessions** table
3. Click the **+** button to add a new field
4. Configure the field:
   - **Field name**: `Garmin URL`
   - **Field type**: URL
   - **Description**: Direct link to activity on Garmin Connect
5. Click **Create field**

## Option 2: Use Airtable REST API

If you prefer to add it programmatically, you can use the Airtable REST API directly:

```bash
curl -X POST "https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{TABLE_ID}/fields" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "name": "Garmin URL",
    "type": "url",
    "description": "Direct link to activity on Garmin Connect"
  }'
```

Replace:
- `{BASE_ID}`: Your Airtable base ID (from `.env`)
- `{TABLE_ID}`: `tblkQ4NBx2r292YEt` (Training Sessions table)
- `YOUR_ACCESS_TOKEN`: Your Airtable Personal Access Token

## Verification

After adding the field, verify it exists:

```bash
python -c "from pyairtable import Api; from core.config import Config; api = Api(Config.AIRTABLE_ACCESS_TOKEN); base = api.base(Config.AIRTABLE_BASE_ID); schema = base.schema(); training_table = [t for t in schema.tables if t.name == Config.AIRTABLE_TRAINING_SESSIONS][0]; print('Training Sessions fields:'); [print(f'  - {f.name} ({f.type})') for f in training_table.fields if 'url' in f.name.lower() or f.type == 'url']"
```

You should see:
```
Training Sessions fields:
  - Garmin URL (url)
```

## Sync Code is Already Updated

The sync code in `airtable/health.py` is already configured to populate this field:

```python
session_data = {
    'Activity ID': external_id,
    'Activity Name': activity.get('title'),
    # ... other fields ...
    'Garmin Link': activity.get('garmin_url'),  # ← This will be mapped to Garmin URL field
}
```

However, I need to update the field name from "Garmin Link" to "Garmin URL" to match what you'll create in Airtable.

## Next Steps

1. Add the "Garmin URL" field to your Training Sessions table (using Option 1 above)
2. I'll update the sync code to use the correct field name
3. Run the sync to populate the field with Garmin activity URLs

Let me know when you've added the field and I'll update the code!
