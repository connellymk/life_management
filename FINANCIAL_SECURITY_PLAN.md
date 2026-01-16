# Financial Integration Security Plan

## Overview

This document outlines the security architecture for integrating Plaid banking data with Notion. Financial data requires the highest level of security, and this plan ensures sensitive information is properly protected.

## Threat Model

### Assets to Protect
1. **Plaid API Credentials** (client_id, secret)
2. **Plaid Access Tokens** (long-lived tokens for accessing bank accounts)
3. **Bank Account Numbers** (full account numbers)
4. **Transaction Details** (amounts, merchants, descriptions)
5. **Personal Identifiable Information** (PII)
6. **Notion API Token** (access to all Notion data)

### Threats
1. **Credential Exposure** - API keys committed to git or exposed in logs
2. **Token Theft** - Access tokens stolen from file system
3. **Data Leakage** - Sensitive data visible in Notion to unauthorized users
4. **Man-in-the-Middle** - API calls intercepted
5. **Local File Access** - Attacker gains access to local machine
6. **Log Exposure** - Sensitive data logged in plain text

## Security Architecture

### 1. Credential Storage

**Environment Variables (.env)**
```
# Never commit this file to git!
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret_key
PLAID_ENVIRONMENT=sandbox  # or development, production
```

**Protection Measures:**
- ✅ `.env` file added to `.gitignore`
- ✅ File permissions set to 600 (owner read/write only)
- ✅ No credentials hardcoded in source code
- ✅ Environment-specific secrets (sandbox vs production)

**Implementation:**
```python
# core/config.py - Secure credential loading
import os
from pathlib import Path
from dotenv import load_dotenv

class PlaidConfig:
    # Load from .env
    load_dotenv()

    PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
    PLAID_SECRET = os.getenv('PLAID_SECRET')
    PLAID_ENVIRONMENT = os.getenv('PLAID_ENVIRONMENT', 'sandbox')

    @classmethod
    def validate(cls):
        """Validate all required credentials are present"""
        required = ['PLAID_CLIENT_ID', 'PLAID_SECRET']
        missing = [k for k in required if not getattr(cls, k)]
        if missing:
            raise ValueError(f"Missing credentials: {missing}")
```

### 2. Access Token Security

**Storage Location:**
- Encrypted SQLite database (`state.db`)
- NOT stored in `.env` or plain text files

**Encryption:**
```python
# core/secure_storage.py
from cryptography.fernet import Fernet
import sqlite3
import os

class SecureTokenStorage:
    def __init__(self):
        # Encryption key derived from machine-specific data
        # OR stored in secure OS keyring
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

    def _get_or_create_key(self):
        """Get encryption key from secure storage"""
        key_file = Path.home() / '.plaid_key'
        if key_file.exists():
            return key_file.read_bytes()
        else:
            # Generate new key (only on first run)
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Owner read/write only
            return key

    def save_access_token(self, item_id: str, access_token: str):
        """Encrypt and store access token"""
        encrypted = self.cipher.encrypt(access_token.encode())
        # Store in database
        conn = sqlite3.connect('state.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO plaid_tokens
            (item_id, encrypted_token, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (item_id, encrypted))
        conn.commit()
        conn.close()

    def get_access_token(self, item_id: str) -> str:
        """Retrieve and decrypt access token"""
        conn = sqlite3.connect('state.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT encrypted_token FROM plaid_tokens WHERE item_id = ?",
            (item_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            encrypted_token = result[0]
            return self.cipher.decrypt(encrypted_token).decode()
        return None
```

### 3. Data Masking in Notion

**Account Numbers:**
- Store ONLY last 4 digits in Notion
- Full account number never leaves local machine

**Example:**
```python
def mask_account_number(account_number: str) -> str:
    """Mask all but last 4 digits"""
    if not account_number or len(account_number) < 4:
        return "****"
    return f"****{account_number[-4:]}"

# In Notion: "Checking ****1234" instead of "Checking 123456789"
```

**Transaction Descriptions:**
- Optionally sanitize merchant names
- Remove specific location details if desired

### 4. API Communication Security

**HTTPS Only:**
```python
class PlaidSync:
    def __init__(self):
        # Plaid SDK enforces HTTPS
        # Additional verification
        self.verify_ssl = True
        self.timeout = 30  # Prevent hanging connections
```

**Certificate Pinning (Optional):**
- For production, consider pinning Plaid's SSL certificate
- Prevents MITM attacks even with compromised CA

### 5. Logging Security

**Sensitive Data Redaction:**
```python
import logging
import re

class SecureFormatter(logging.Formatter):
    """Custom formatter that redacts sensitive data"""

    PATTERNS = [
        (re.compile(r'"client_id":\s*"[^"]*"'), '"client_id": "[REDACTED]"'),
        (re.compile(r'"secret":\s*"[^"]*"'), '"secret": "[REDACTED]"'),
        (re.compile(r'"access_token":\s*"[^"]*"'), '"access_token": "[REDACTED]"'),
        (re.compile(r'\d{9,}'), '[ACCOUNT_REDACTED]'),  # Account numbers
        (re.compile(r'"account_id":\s*"[^"]*"'), '"account_id": "[REDACTED]"'),
    ]

    def format(self, record):
        msg = super().format(record)
        for pattern, replacement in self.PATTERNS:
            msg = pattern.sub(replacement, msg)
        return msg

# Usage
logger = logging.getLogger('plaid_sync')
handler = logging.FileHandler('logs/sync.log')
handler.setFormatter(SecureFormatter())
logger.addHandler(handler)
```

**Log File Permissions:**
```bash
# Set restrictive permissions on log files
chmod 600 logs/*.log
```

### 6. Database Security

**State Database:**
```sql
-- Create tables with proper structure
CREATE TABLE IF NOT EXISTS plaid_tokens (
    item_id TEXT PRIMARY KEY,
    encrypted_token BLOB NOT NULL,  -- Encrypted access token
    institution_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance (not security)
CREATE INDEX idx_institution ON plaid_tokens(institution_id);
```

**File Permissions:**
```bash
chmod 600 state.db  # Owner read/write only
```

### 7. Notion Data Protection

**What Goes in Notion (Public/Shared):**
- ✅ Transaction date, amount, category
- ✅ Merchant name (generalized)
- ✅ Account nickname (e.g., "Primary Checking")
- ✅ Masked account number (last 4 digits)
- ✅ Current balances
- ✅ Investment tickers and values

**What NEVER Goes in Notion:**
- ❌ Full account numbers
- ❌ Routing numbers
- ❌ SSN or other PII
- ❌ Full transaction descriptions with locations
- ❌ Plaid access tokens
- ❌ Bank login credentials

**Notion Database Sharing:**
```
⚠️ IMPORTANT: Only share Notion financial databases with:
- Yourself (primary account)
- Trusted family members with explicit permission
- NEVER share publicly or with Claude integrations you don't control
```

### 8. Error Handling

**No Sensitive Data in Errors:**
```python
try:
    response = plaid_client.transactions_get(access_token)
except PlaidError as e:
    # DON'T LOG: e.display_message (may contain sensitive data)
    # DO LOG: Generic error type
    logger.error(f"Plaid API error: {e.type} - {e.code}")
    # Don't expose details to user
    raise Exception("Failed to fetch transactions. Check logs.")
```

### 9. Access Control

**Local Machine Security:**
```bash
# Ensure only your user can access the project
chmod 700 personal_assistant/
chmod 600 personal_assistant/.env
chmod 600 personal_assistant/state.db
```

**Multi-User Systems:**
- Store credentials in user-specific directory
- Use OS keyring for encryption keys (optional)

### 10. Plaid-Specific Security

**Link Token Usage:**
```python
# Use short-lived link tokens for initial auth
# Never reuse or store link tokens
link_token = plaid_client.link_token_create({
    'user': {'client_user_id': 'user_id'},
    'products': ['transactions', 'investments'],
    'language': 'en',
})
# Link token expires in 4 hours - perfect for one-time use
```

**Access Token Rotation:**
```python
# Plaid access tokens don't expire, but can be rotated
def rotate_access_token(old_access_token: str):
    """Rotate access token for additional security"""
    response = plaid_client.item_access_token_invalidate(old_access_token)
    new_token = response['new_access_token']
    # Save new token, delete old one
    return new_token
```

## Security Checklist

Before going to production:

- [ ] All credentials in `.env`, not hardcoded
- [ ] `.env` in `.gitignore`
- [ ] Access tokens encrypted in state.db
- [ ] State.db file permissions set to 600
- [ ] Encryption key stored securely
- [ ] Account numbers masked in Notion (last 4 only)
- [ ] Logging redacts sensitive data
- [ ] Log files have restrictive permissions
- [ ] HTTPS enforced for all API calls
- [ ] Error messages don't expose sensitive data
- [ ] Notion databases not shared publicly
- [ ] Project directory has restrictive permissions
- [ ] Tested with Plaid sandbox before production
- [ ] Production credentials separate from sandbox

## Incident Response

**If credentials are compromised:**

1. **Immediately:**
   - Rotate Plaid API keys in dashboard
   - Invalidate all access tokens
   - Change Notion API token
   - Update `.env` with new credentials

2. **Investigation:**
   - Check git history for accidental commits
   - Review log files for unauthorized access
   - Check Notion audit log for suspicious activity

3. **Prevention:**
   - Review `.gitignore` rules
   - Audit file permissions
   - Enable Plaid webhook notifications

## Compliance Considerations

**Data Retention:**
- Keep transactions for 7 years (tax purposes)
- Delete old access tokens after account disconnection
- Purge logs older than 90 days

**User Consent:**
- Document what data is collected
- Explain how data is stored (Notion + local)
- Provide way to delete all financial data

## Alternative: OS Keyring (Enhanced Security)

For maximum security, store encryption key in OS keyring:

```python
import keyring

# Store encryption key in OS keyring
keyring.set_password("plaid_sync", "encryption_key", key.decode())

# Retrieve
key = keyring.get_password("plaid_sync", "encryption_key").encode()
```

**Benefits:**
- OS-level encryption
- Protected by user login credentials
- Not accessible if machine is compromised while logged out

## Recommended Security Posture

**For Personal Use (You):**
- ✅ Encrypted access tokens in local database
- ✅ Masked account numbers in Notion
- ✅ Credentials in `.env` (not committed to git)
- ✅ Logging with sensitive data redaction
- ⚠️ Consider OS keyring for encryption key

**For Shared/Family Use:**
- ✅ All of the above
- ✅ OS keyring for encryption key (required)
- ✅ Separate Notion workspace or restricted sharing
- ✅ Audit logs enabled in Notion

**For Public/Open Source:**
- ❌ Don't implement - too risky for open source
- Financial integrations should remain private

---

**Next Steps:**
1. Review this plan and approve
2. Implement secure credential storage
3. Set up encryption for access tokens
4. Create Notion databases with masked data only
5. Test with Plaid sandbox
6. Audit security before production use
