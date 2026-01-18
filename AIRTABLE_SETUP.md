# Airtable Setup Guide

## Quick Start

### 1. Create Personal Access Token

Airtable now uses Personal Access Tokens (PATs) for API authentication instead of API keys.

**Steps:**
1. Visit https://airtable.com/create/tokens
2. Click **"Create new token"**
3. Configure your token:
   - **Name**: `Personal Assistant Sync` (or any descriptive name)
   - **Scopes** (required):
     - ✅ `data.records:read` - Read records from tables
     - ✅ `data.records:write` - Create and update records
     - ✅ `schema.bases:read` - Read base structure
   - **Access**: Select your personal assistant base
4. Click **"Create token"**
5. **IMPORTANT**: Copy the token immediately - it starts with `pat_` and you won't be able to see it again!

### 2. Get Your Base ID

Your Base ID is in your Airtable base URL:
```
https://airtable.com/appXXXXXXXXXXXXXX/...
                      ^^^^^^^^^^^^^^^^^^
                      This is your Base ID
```

The Base ID always starts with `app` and is 17 characters long.

### 3. Configure Environment Variables

Edit your `.env` file:

```bash
# Airtable Personal Access Token
AIRTABLE_ACCESS_TOKEN=pat_your_actual_token_here

# Airtable Base ID
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

### 4. Verify Connection

Test your configuration:

```python
from airtable.base_client import AirtableClient

# This will raise an error if credentials are invalid
client = AirtableClient()
print("✅ Connected to Airtable successfully!")

# Test accessing a table
day_table = client.get_day_table()
print(f"✅ Can access Day table")
```

## Security Best Practices

### Token Security
- ✅ **Never commit** your Personal Access Token to git
- ✅ **Use `.env` files** (already in `.gitignore`)
- ✅ **Scope tokens** to only the base you need
- ✅ **Set expiration dates** on tokens when possible
- ✅ **Rotate tokens** periodically for security

### Token Scopes
Only grant the minimum required scopes:
- `data.records:read` - If you only need to read data
- `data.records:write` - If you need to create/update records
- `schema.bases:read` - If you need to inspect table structure
- ❌ Avoid `data.records:delete` unless absolutely necessary

### Multiple Bases
If you have multiple Airtable bases, create separate tokens for each with appropriate scopes.

## Advantages of Personal Access Tokens

### vs Legacy API Keys

| Feature | Personal Access Token | Legacy API Key |
|---------|----------------------|----------------|
| **Security** | Scoped to specific bases | Access to all bases |
| **Granularity** | Choose specific permissions | Full read/write access |
| **Expiration** | Can set expiration dates | Never expires |
| **Revocation** | Easy to revoke individual tokens | Revokes all API access |
| **Status** | ✅ Recommended by Airtable | ⚠️ Deprecated |

### Token Management
- View all your tokens at https://airtable.com/account
- Revoke compromised tokens immediately
- Create separate tokens for development and production
- Name tokens descriptively (e.g., "Dev Laptop", "Production Server")

## Troubleshooting

### "Invalid token" error
- ✅ Check token starts with `pat_`
- ✅ Verify token hasn't been revoked
- ✅ Ensure token has access to your base
- ✅ Check required scopes are granted

### "Base not found" error
- ✅ Verify Base ID starts with `app`
- ✅ Check token has access to this base
- ✅ Ensure Base ID is exactly 17 characters

### "Insufficient permissions" error
- ✅ Add required scopes to your token
- ✅ Re-create token if scopes can't be modified
- ✅ Check you have permissions to the base in Airtable

### Rate Limit Errors
- Airtable allows 5 requests per second per base
- Use batch operations when possible
- Implement exponential backoff for retries
- See: https://airtable.com/developers/web/api/rate-limits

## Migration from API Keys

If you're migrating from legacy API keys:

1. **Create a Personal Access Token** (see steps above)
2. **Update `.env` file**:
   ```bash
   # Old (deprecated)
   # AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX

   # New (recommended)
   AIRTABLE_ACCESS_TOKEN=pat_XXXXXXXXXXXXXXXX
   ```
3. **Test the integration** with new token
4. **Remove API key** from Airtable account once confirmed working

Our code supports both for backward compatibility, but will prefer Personal Access Token.

## Resources

- **Create Tokens**: https://airtable.com/create/tokens
- **Manage Tokens**: https://airtable.com/account
- **API Documentation**: https://airtable.com/developers/web/api/introduction
- **Rate Limits**: https://airtable.com/developers/web/api/rate-limits
- **Python Library**: https://pyairtable.readthedocs.io/

## Next Steps

After setting up authentication:
1. ✅ Create Day and Week dimension tables in your base
2. ✅ Create data tables (Calendar Events, Training Sessions, etc.)
3. ✅ Test connection with provided Python client
4. ✅ Run initial sync to populate tables
5. ✅ Set up automated syncs

See `airtable_structure_plan.md` for complete table schema and field definitions.
