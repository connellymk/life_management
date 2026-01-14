# Credentials Directory

This directory stores OAuth credentials and tokens. **Never commit these files to git!**

## Required Files

### For Google Calendar Integration:
- `google_client_secret.json` - OAuth client credentials from Google Cloud Console
- `google_token.json` - Generated automatically after first authentication

### For Microsoft Calendar Integration (Future):
- `ms_token.json` - Generated automatically after first authentication

### For Strava Integration (Future):
- `strava_token.json` - Generated automatically after first authentication

## Setup Instructions

See the main README.md and SETUP_GUIDES.md for detailed instructions on obtaining these credentials.

## Security Notes

- All credential files are automatically ignored by git (see .gitignore)
- Keep these files secure and never share them
- If credentials are compromised, revoke and regenerate them immediately
- Use read-only scopes where possible for enhanced security
