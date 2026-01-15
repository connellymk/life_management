#!/usr/bin/env python3
"""
Automated migration script for personal_assistant refactor.
Migrates from separate calendar-sync and health-training modules
to unified structure with shared core.

Usage:
    python migrate.py --dry-run    # Preview changes
    python migrate.py              # Execute migration
"""

import os
import sys
import shutil
import re
from pathlib import Path
from typing import List, Tuple

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


class Migrator:
    """Handles migration from old structure to new unified structure."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.base_dir = Path(__file__).parent
        self.changes: List[str] = []
        self.errors: List[str] = []

    def log(self, message: str, color: str = ""):
        """Log a message."""
        print(f"{color}{message}{RESET}")
        self.changes.append(message)

    def error(self, message: str):
        """Log an error."""
        print(f"{RED}✗ ERROR: {message}{RESET}")
        self.errors.append(message)

    def copy_and_update_file(self, src: Path, dest: Path, import_updates: dict):
        """
        Copy file and update import statements.

        Args:
            src: Source file path
            dest: Destination file path
            import_updates: Dict of old import -> new import replacements
        """
        if not src.exists():
            self.error(f"Source file not found: {src}")
            return

        # Read source file
        with open(src, 'r') as f:
            content = f.read()

        # Update imports
        for old_import, new_import in import_updates.items():
            content = content.replace(old_import, new_import)

        # Write to destination
        if not self.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, 'w') as f:
                f.write(content)

        self.log(f"  ✓ Migrated: {src.name} -> {dest.relative_to(self.base_dir)}", GREEN)

    def step1_create_core_utils(self):
        """Step 1: Create unified core/utils.py"""
        self.log(f"\n{BLUE}Step 1: Creating core/utils.py{RESET}")

        # Merge utils from both modules
        calendar_utils = self.base_dir / "calendar-sync/src/utils.py"
        health_utils = self.base_dir / "health-training/src/utils.py"

        if not calendar_utils.exists():
            self.error(f"Calendar utils not found: {calendar_utils}")
            return

        # For now, use calendar-sync utils as base (it's more complete)
        import_updates = {
            "from src.config import Config": "from core.config import Config",
        }

        dest = self.base_dir / "core/utils.py"
        self.copy_and_update_file(calendar_utils, dest, import_updates)

    def step2_create_core_config(self):
        """Step 2: Create unified core/config.py"""
        self.log(f"\n{BLUE}Step 2: Creating core/config.py{RESET}")

        dest = self.base_dir / "core/config.py"

        if self.dry_run:
            self.log(f"  Would create: {dest.relative_to(self.base_dir)}", YELLOW)
            return

        # Create base config class
        config_content = '''"""
Unified configuration management for all integrations.
Loads from single .env file at project root.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from project root
BASE_DIR = Path(__file__).parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Base configuration class."""

    # Notion (shared across all integrations)
    NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

    # Notion Database IDs
    NOTION_CALENDAR_DB_ID = os.getenv("NOTION_CALENDAR_DB_ID", "")
    NOTION_WORKOUTS_DB_ID = os.getenv("NOTION_WORKOUTS_DB_ID", "")
    NOTION_DAILY_METRICS_DB_ID = os.getenv("NOTION_DAILY_METRICS_DB_ID", "")
    NOTION_BODY_METRICS_DB_ID = os.getenv("NOTION_BODY_METRICS_DB_ID", "")

    # Google Calendar
    GOOGLE_CALENDAR_IDS = os.getenv("GOOGLE_CALENDAR_IDS", "primary")
    GOOGLE_CALENDAR_NAMES = os.getenv("GOOGLE_CALENDAR_NAMES", "Personal")

    # Garmin
    GARMIN_EMAIL = os.getenv("GARMIN_EMAIL", "")
    GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD", "")

    # Sync settings
    SYNC_LOOKBACK_DAYS = int(os.getenv("SYNC_LOOKBACK_DAYS", "90"))
    SYNC_LOOKAHEAD_DAYS = int(os.getenv("SYNC_LOOKAHEAD_DAYS", "365"))
    UNIT_SYSTEM = os.getenv("UNIT_SYSTEM", "imperial").lower()

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> tuple[bool, List[str]]:
        """
        Validate configuration.

        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors = []

        # Check Notion token
        if not cls.NOTION_TOKEN:
            errors.append("NOTION_TOKEN not set in .env file")
        elif not (cls.NOTION_TOKEN.startswith("secret_") or cls.NOTION_TOKEN.startswith("ntn_")):
            errors.append("NOTION_TOKEN should start with 'secret_' or 'ntn_'")

        return len(errors) == 0, errors


class GoogleCalendarConfig(Config):
    """Google Calendar specific configuration."""

    @classmethod
    def validate(cls) -> tuple[bool, List[str]]:
        """Validate Google Calendar configuration."""
        is_valid, errors = super().validate()

        if not cls.NOTION_CALENDAR_DB_ID:
            errors.append("NOTION_CALENDAR_DB_ID not set")

        return len(errors) == 0, errors


class GarminConfig(Config):
    """Garmin specific configuration."""

    @classmethod
    def validate(cls) -> tuple[bool, List[str]]:
        """Validate Garmin configuration."""
        is_valid, errors = super().validate()

        if not cls.GARMIN_EMAIL:
            errors.append("GARMIN_EMAIL not set")
        if not cls.GARMIN_PASSWORD:
            errors.append("GARMIN_PASSWORD not set")

        for db_id, name in [
            (cls.NOTION_WORKOUTS_DB_ID, "NOTION_WORKOUTS_DB_ID"),
            (cls.NOTION_DAILY_METRICS_DB_ID, "NOTION_DAILY_METRICS_DB_ID"),
            (cls.NOTION_BODY_METRICS_DB_ID, "NOTION_BODY_METRICS_DB_ID"),
        ]:
            if not db_id:
                errors.append(f"{name} not set")

        return len(errors) == 0, errors
'''

        with open(dest, 'w') as f:
            f.write(config_content)

        self.log(f"  ✓ Created: {dest.relative_to(self.base_dir)}", GREEN)

    def step3_migrate_google_calendar(self):
        """Step 3: Migrate Google Calendar integration"""
        self.log(f"\n{BLUE}Step 3: Migrating Google Calendar integration{RESET}")

        import_updates = {
            "from src.config import Config": "from core.config import GoogleCalendarConfig as Config",
            "from src.utils import": "from core.utils import",
            "from src.state_manager import StateManager": "from core.state_manager import StateManager",
        }

        # Migrate google_sync.py
        src = self.base_dir / "calendar-sync/src/google_sync.py"
        dest = self.base_dir / "integrations/google_calendar/sync.py"
        self.copy_and_update_file(src, dest, import_updates)

        # Create __init__.py
        init_file = self.base_dir / "integrations/google_calendar/__init__.py"
        if not self.dry_run:
            init_file.write_text('from .sync import GoogleCalendarSync\n\n__all__ = ["GoogleCalendarSync"]\n')
        self.log(f"  ✓ Created: {init_file.relative_to(self.base_dir)}", GREEN)

    def step4_migrate_garmin(self):
        """Step 4: Migrate Garmin integration"""
        self.log(f"\n{BLUE}Step 4: Migrating Garmin integration{RESET}")

        import_updates = {
            "from src.config import Config": "from core.config import GarminConfig as Config",
            "from src.utils import": "from core.utils import",
            "from src.state_manager import StateManager": "from core.state_manager import StateManager",
        }

        # Migrate garmin_sync.py
        src = self.base_dir / "health-training/src/garmin_sync.py"
        dest = self.base_dir / "integrations/garmin/sync.py"
        self.copy_and_update_file(src, dest, import_updates)

        # Create __init__.py
        init_file = self.base_dir / "integrations/garmin/__init__.py"
        if not self.dry_run:
            init_file.write_text('from .sync import GarminSync\n\n__all__ = ["GarminSync"]\n')
        self.log(f"  ✓ Created: {init_file.relative_to(self.base_dir)}", GREEN)

    def step5_create_notion_clients(self):
        """Step 5: Create Notion database clients"""
        self.log(f"\n{BLUE}Step 5: Creating Notion database clients{RESET}")

        # Migrate calendar notion_sync.py
        import_updates = {
            "from src.config import Config": "from core.config import Config",
            "from src.state_manager import StateManager": "from core.state_manager import StateManager",
            "from src.utils import": "from core.utils import",
        }

        src = self.base_dir / "calendar-sync/src/notion_sync.py"
        dest = self.base_dir / "notion/calendar.py"
        self.copy_and_update_file(src, dest, import_updates)

        # Migrate health notion_sync.py
        src = self.base_dir / "health-training/src/notion_sync.py"
        dest = self.base_dir / "notion/health.py"
        self.copy_and_update_file(src, dest, import_updates)

    def step6_create_env_template(self):
        """Step 6: Create unified .env.example"""
        self.log(f"\n{BLUE}Step 6: Creating unified .env.example{RESET}")

        env_content = '''# ==================== Notion ====================
NOTION_TOKEN=ntn_your_token_here

# Calendar Events Database
NOTION_CALENDAR_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Health Databases
NOTION_WORKOUTS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DAILY_METRICS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_BODY_METRICS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ==================== Google Calendar ====================
GOOGLE_CALENDAR_IDS=primary
GOOGLE_CALENDAR_NAMES=Personal

SYNC_LOOKBACK_DAYS=90
SYNC_LOOKAHEAD_DAYS=365

# ==================== Garmin ====================
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password

# ==================== Settings ====================
UNIT_SYSTEM=imperial
LOG_LEVEL=INFO
'''

        dest = self.base_dir / ".env.example"
        if not self.dry_run:
            with open(dest, 'w') as f:
                f.write(env_content)

        self.log(f"  ✓ Created: {dest.relative_to(self.base_dir)}", GREEN)

    def step7_create_gitignore(self):
        """Step 7: Create unified .gitignore"""
        self.log(f"\n{BLUE}Step 7: Creating unified .gitignore{RESET}")

        gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Environment variables
.env

# Credentials
credentials/
*.json
*.oauth

# Logs
logs/
*.log

# State database
state.db
*.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Archive
_archive/
'''

        dest = self.base_dir / ".gitignore"
        if not self.dry_run:
            with open(dest, 'w') as f:
                f.write(gitignore_content)

        self.log(f"  ✓ Created: {dest.relative_to(self.base_dir)}", GREEN)

    def step8_merge_env_files(self):
        """Step 8: Merge existing .env files"""
        self.log(f"\n{BLUE}Step 8: Merging .env files{RESET}")

        calendar_env = self.base_dir / "calendar-sync/.env"
        health_env = self.base_dir / "health-training/.env"
        dest_env = self.base_dir / ".env"

        if dest_env.exists():
            self.log(f"  ⚠ .env already exists, skipping merge", YELLOW)
            self.log(f"    You'll need to manually merge credentials", YELLOW)
            return

        if not self.dry_run:
            env_content = "# Merged from calendar-sync and health-training\n\n"

            # Copy from calendar-sync
            if calendar_env.exists():
                env_content += "# From calendar-sync\n"
                env_content += calendar_env.read_text()
                env_content += "\n\n"

            # Copy from health-training
            if health_env.exists():
                env_content += "# From health-training\n"
                env_content += health_env.read_text()

            dest_env.write_text(env_content)

        self.log(f"  ✓ Created: {dest_env.relative_to(self.base_dir)}", GREEN)
        self.log(f"    Review and clean up duplicate entries!", YELLOW)

    def step9_archive_old_modules(self):
        """Step 9: Archive old module directories"""
        self.log(f"\n{BLUE}Step 9: Archiving old modules{RESET}")

        archive_dir = self.base_dir / "_archive"

        for module in ["calendar-sync", "health-training"]:
            src = self.base_dir / module
            dest = archive_dir / module

            if not src.exists():
                self.log(f"  Module {module} not found, skipping", YELLOW)
                continue

            if self.dry_run:
                self.log(f"  Would move: {module} -> _archive/{module}", YELLOW)
            else:
                archive_dir.mkdir(exist_ok=True)
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(src), str(dest))
                self.log(f"  ✓ Archived: {module} -> _archive/{module}", GREEN)

    def run(self):
        """Run the migration."""
        self.log(f"\n{'='*60}")
        self.log(f"Personal Assistant Migration Script")
        self.log(f"{'='*60}")

        if self.dry_run:
            self.log(f"\n{YELLOW}DRY RUN MODE - No files will be modified{RESET}\n")
        else:
            self.log(f"\n{RED}LIVE MODE - Files will be modified{RESET}\n")
            response = input("Continue? (yes/no): ")
            if response.lower() != "yes":
                self.log("Migration cancelled")
                return

        # Run migration steps
        try:
            self.step1_create_core_utils()
            self.step2_create_core_config()
            self.step3_migrate_google_calendar()
            self.step4_migrate_garmin()
            self.step5_create_notion_clients()
            self.step6_create_env_template()
            self.step7_create_gitignore()
            self.step8_merge_env_files()
            self.step9_archive_old_modules()

        except Exception as e:
            self.error(f"Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # Summary
        self.log(f"\n{'='*60}")
        if self.errors:
            self.log(f"{RED}Migration completed with {len(self.errors)} errors:{RESET}")
            for error in self.errors:
                self.log(f"  - {error}", RED)
        else:
            self.log(f"{GREEN}✓ Migration completed successfully!{RESET}")

        if not self.dry_run:
            self.log(f"\n{BLUE}Next steps:{RESET}")
            self.log(f"  1. Review merged .env file")
            self.log(f"  2. Create virtual environment: python3 -m venv venv")
            self.log(f"  3. Install dependencies: pip install -r requirements.txt")
            self.log(f"  4. Test: python scripts/test_auth.py")
            self.log(f"  5. See MIGRATION_GUIDE.md for details")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate personal_assistant to unified structure")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    args = parser.parse_args()

    migrator = Migrator(dry_run=args.dry_run)
    migrator.run()


if __name__ == "__main__":
    main()
