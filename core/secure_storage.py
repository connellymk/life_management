"""
Secure storage for sensitive credentials and tokens.
Uses Fernet encryption to protect access tokens at rest.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class SecureTokenStorage:
    """
    Encrypted storage for Plaid access tokens.

    Security features:
    - Fernet symmetric encryption
    - Encryption key stored separately with restrictive permissions
    - Access tokens never stored in plain text
    - Database file permissions set to 600 (owner only)
    """

    def __init__(self, db_path: str = "state.db", key_path: Optional[str] = None):
        """
        Initialize secure token storage.

        Args:
            db_path: Path to SQLite database
            key_path: Path to encryption key file (defaults to ~/.plaid_key)
        """
        self.db_path = db_path
        self.key_path = key_path or str(Path.home() / ".plaid_key")

        # Initialize encryption
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

        # Initialize database
        self._init_database()

        logger.info("Initialized secure token storage")

    def _get_or_create_key(self) -> bytes:
        """
        Get encryption key from file or create new one.

        Returns:
            Encryption key bytes
        """
        key_file = Path(self.key_path)

        if key_file.exists():
            logger.info(f"Loading encryption key from {self.key_path}")
            return key_file.read_bytes()
        else:
            logger.info(f"Generating new encryption key at {self.key_path}")
            key = Fernet.generate_key()
            key_file.write_bytes(key)

            # Set restrictive permissions (owner read/write only)
            try:
                key_file.chmod(0o600)
            except Exception as e:
                logger.warning(f"Could not set key file permissions: {e}")

            return key

    def _init_database(self):
        """
        Initialize database tables for encrypted tokens.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create plaid_tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plaid_tokens (
                item_id TEXT PRIMARY KEY,
                encrypted_token BLOB NOT NULL,
                institution_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_institution
            ON plaid_tokens(institution_name)
        """)

        conn.commit()
        conn.close()

        # Set restrictive permissions on database file
        try:
            Path(self.db_path).chmod(0o600)
        except Exception as e:
            logger.warning(f"Could not set database file permissions: {e}")

    def save_access_token(
        self, item_id: str, access_token: str, institution_name: str = ""
    ):
        """
        Encrypt and store access token.

        Args:
            item_id: Plaid item ID
            access_token: Plaid access token (will be encrypted)
            institution_name: Institution name for reference
        """
        # Encrypt the token
        encrypted = self.cipher.encrypt(access_token.encode())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO plaid_tokens
            (item_id, encrypted_token, institution_name, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (item_id, encrypted, institution_name),
        )

        conn.commit()
        conn.close()

        logger.info(f"Saved encrypted access token for item {item_id}")

    def get_access_token(self, item_id: str) -> Optional[str]:
        """
        Retrieve and decrypt access token.

        Args:
            item_id: Plaid item ID

        Returns:
            Decrypted access token or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT encrypted_token FROM plaid_tokens WHERE item_id = ?", (item_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            encrypted_token = result[0]
            try:
                decrypted = self.cipher.decrypt(encrypted_token).decode()
                logger.debug(f"Retrieved access token for item {item_id}")
                return decrypted
            except Exception as e:
                logger.error(f"Failed to decrypt token for {item_id}: {e}")
                return None

        logger.warning(f"No access token found for item {item_id}")
        return None

    def delete_access_token(self, item_id: str):
        """
        Delete access token from storage.

        Args:
            item_id: Plaid item ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM plaid_tokens WHERE item_id = ?", (item_id,))
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        if deleted:
            logger.info(f"Deleted access token for item {item_id}")
        else:
            logger.warning(f"No token found to delete for item {item_id}")

    def get_all_items(self) -> List[str]:
        """
        Get list of all stored item IDs.

        Returns:
            List of item IDs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT item_id FROM plaid_tokens")
        items = [row[0] for row in cursor.fetchall()]

        conn.close()

        logger.debug(f"Found {len(items)} stored items")
        return items

    def get_institution_items(self, institution_name: str) -> List[str]:
        """
        Get all item IDs for a specific institution.

        Args:
            institution_name: Institution name

        Returns:
            List of item IDs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT item_id FROM plaid_tokens WHERE institution_name = ?",
            (institution_name,),
        )
        items = [row[0] for row in cursor.fetchall()]

        conn.close()

        return items

    def rotate_access_token(self, item_id: str, new_access_token: str):
        """
        Rotate access token (for security best practices).

        Args:
            item_id: Plaid item ID
            new_access_token: New access token to store
        """
        # Simply save the new token (will replace old one)
        self.save_access_token(item_id, new_access_token)
        logger.info(f"Rotated access token for item {item_id}")
