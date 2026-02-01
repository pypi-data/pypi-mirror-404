"""
Alembic migration manager for programmatic schema migrations.

This module provides a programmatic interface to Alembic for managing
database schema migrations without requiring manual configuration files.
"""

import os
import shutil
import re
from typing import List, Dict, Any, Optional
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import MetaData, create_engine, inspect
from sqlalchemy.exc import ProgrammingError
from ..exceptions.sql_exceptions import MigrationError


class AlembicManager:
    """
    Manages Alembic migrations programmatically.

    This class provides methods to initialize Alembic, generate migrations,
    apply/rollback migrations, and query migration status without requiring
    manual alembic.ini or env.py configuration.

    Attributes:
        connection_string: Database connection string
        migrations_dir: Directory path for migration files
        metadata: SQLAlchemy MetaData object
        config: Alembic Config object
    """

    def __init__(
        self,
        connection_string: str,
        migrations_dir: str,
        metadata: MetaData,
        schema: Optional[str] = None
    ):
        """
        Initialize Alembic manager.

        Args:
            connection_string: SQLAlchemy connection string
            migrations_dir: Directory for migration files
            metadata: SQLAlchemy MetaData for autogeneration
            schema: Database schema for migrations (PostgreSQL)
        """
        self.connection_string = connection_string
        self.migrations_dir = migrations_dir
        self.metadata = metadata
        self.schema = schema
        self.config = self._create_config()

    def _create_config(self) -> Config:
        """
        Create Alembic configuration object programmatically.

        Returns:
            Configured Alembic Config object
        """
        config = Config()
        # Set config file name for command.init() to work properly
        config.config_file_name = os.path.join(self.migrations_dir, "alembic.ini")
        config.set_main_option("script_location", self.migrations_dir)

        # Escape % characters in connection string for ConfigParser
        # ConfigParser uses % for interpolation, so we need to escape it as %%
        escaped_connection_string = self.connection_string.replace("%", "%%")
        config.set_main_option("sqlalchemy.url", escaped_connection_string)

        # Set additional configuration options
        config.set_main_option("file_template", "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s")
        config.set_main_option("truncate_slug_length", "40")
        config.set_main_option("timezone", "UTC")

        return config

    def init(self) -> None:
        """
        Initialize Alembic directory structure.

        Creates the migrations directory with necessary files including
        alembic.ini, env.py, script.py.mako, and README.

        If the directory already exists, ensures env.py is properly configured
        without recreating the entire structure.

        Raises:
            MigrationError: If initialization fails
        """
        try:
            if os.path.exists(self.migrations_dir):
                # Directory exists - skip init but ensure env.py is configured
                print(f"Migrations directory exists at {self.migrations_dir}, ensuring env.py is configured...")
                self._customize_env_py()
            else:
                # Fresh initialization
                print(f"Initializing new migrations directory at {self.migrations_dir}...")
                command.init(self.config, self.migrations_dir)
                self._customize_env_py()

        except Exception as e:
            raise MigrationError(f"Failed to initialize Alembic: {str(e)}")

    def _customize_env_py(self) -> None:
        """
        Customize env.py to use the provided metadata object.

        This replaces the default env.py with a version that uses the
        metadata from the SQLManager instead of requiring manual import.

        Creates a backup of existing env.py before overwriting.
        """
        env_path = os.path.join(self.migrations_dir, "env.py")

        # Create backup of existing env.py if it exists
        if os.path.exists(env_path):
            backup_path = env_path + ".backup"
            if not os.path.exists(backup_path):
                shutil.copy(env_path, backup_path)
                print(f"Backed up existing env.py to {backup_path}")

        # Add schema configuration if specified
        schema_config = f'"{self.schema}"' if self.schema else 'None'

        env_template = f'''"""
Alembic environment configuration.

This file was generated programmatically by SQLManager.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your Base metadata here
# For SQLManager, this will be set programmatically
from SQLManager.models.base import Base
target_metadata = Base.metadata

# Schema configuration
target_schema = {schema_config}


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
        version_table_schema=target_schema,
        include_schemas=True if target_schema else False,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=target_schema,
            include_schemas=True if target_schema else False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

        with open(env_path, 'w') as f:
            f.write(env_template)

    def create_migration(
        self,
        message: str,
        autogenerate: bool = True
    ) -> str:
        """
        Create a new migration file.

        Args:
            message: Migration message/description
            autogenerate: If True, auto-detect schema changes from metadata

        Returns:
            Revision ID of the created migration

        Raises:
            MigrationError: If migration creation fails
        """
        try:
            # Generate migration
            command.revision(
                self.config,
                message=message,
                autogenerate=autogenerate
            )

            # Get the latest revision ID
            return self._get_latest_revision()

        except Exception as e:
            raise MigrationError(f"Failed to create migration: {str(e)}")

    def upgrade(self, revision: str = "head", safe_mode: bool = False) -> None:
        """
        Upgrade database to a specific revision.

        Args:
            revision: Target revision ("head" for latest, "+1" for one step, or specific revision ID)
            safe_mode: If True, skip migrations that fail due to existing tables

        Raises:
            MigrationError: If upgrade fails
        """
        try:
            command.upgrade(self.config, revision)
        except Exception as e:
            error_msg = str(e)

            # Check if this is a duplicate table/column error
            if safe_mode and ("already exists" in error_msg or "DuplicateTable" in error_msg or "DuplicateColumn" in error_msg):
                print(f"⚠️  Warning: Skipping migration due to existing objects: {error_msg}")
                print("💡 Tip: Consider using stamp() to mark migrations as applied without running them")
                return

            raise MigrationError(f"Failed to upgrade migrations: {str(e)}")

    def downgrade(self, revision: str = "-1") -> None:
        """
        Downgrade database to a previous revision.

        Args:
            revision: Target revision ("-1" for one step back, "base" for initial, or specific revision ID)

        Raises:
            MigrationError: If downgrade fails
        """
        try:
            command.downgrade(self.config, revision)
        except Exception as e:
            raise MigrationError(f"Failed to downgrade migrations: {str(e)}")

    def current(self) -> Optional[str]:
        """
        Get the current migration revision.

        Returns:
            Current revision ID or None if no migrations applied

        Raises:
            MigrationError: If unable to determine current revision
        """
        try:
            engine = create_engine(self.connection_string)
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()
                return current_rev
        except Exception as e:
            raise MigrationError(f"Failed to get current revision: {str(e)}")

    def history(self) -> List[Dict[str, Any]]:
        """
        Get migration history.

        Returns:
            List of migration dictionaries with revision, message, and other info

        Raises:
            MigrationError: If unable to retrieve history
        """
        try:
            script = ScriptDirectory.from_config(self.config)
            history = []

            for revision in script.walk_revisions():
                history.append({
                    "revision": revision.revision,
                    "down_revision": revision.down_revision,
                    "message": revision.doc,
                    "branch_labels": revision.branch_labels,
                })

            return history

        except Exception as e:
            raise MigrationError(f"Failed to get migration history: {str(e)}")

    def _get_latest_revision(self) -> str:
        """
        Get the latest (head) revision ID.

        Returns:
            Latest revision ID

        Raises:
            MigrationError: If no revisions exist
        """
        try:
            script = ScriptDirectory.from_config(self.config)
            head = script.get_current_head()

            if head is None:
                raise MigrationError("No migrations exist")

            return head

        except Exception as e:
            raise MigrationError(f"Failed to get latest revision: {str(e)}")

    def stamp(self, revision: str = "head") -> None:
        """
        Stamp the database with a specific revision without running migrations.

        This is useful for marking an existing database as being at a specific
        migration version without actually running the migrations.

        Args:
            revision: Revision to stamp ("head" for latest)

        Raises:
            MigrationError: If stamp fails
        """
        try:
            command.stamp(self.config, revision)
        except Exception as e:
            raise MigrationError(f"Failed to stamp revision: {str(e)}")

    def show(self, revision: str = "head") -> str:
        """
        Show the migration script for a specific revision.

        Args:
            revision: Revision ID to show

        Returns:
            Migration script content as string

        Raises:
            MigrationError: If unable to show revision
        """
        try:
            script = ScriptDirectory.from_config(self.config)
            revision_obj = script.get_revision(revision)

            if revision_obj is None:
                raise MigrationError(f"Revision not found: {revision}")

            with open(revision_obj.path, 'r') as f:
                return f.read()

        except Exception as e:
            raise MigrationError(f"Failed to show revision: {str(e)}")

    def detect_duplicate_migrations(self) -> List[str]:
        """
        Detect duplicate migration files by comparing their content.

        Returns:
            List of duplicate migration file paths to remove

        Raises:
            MigrationError: If unable to detect duplicates
        """
        try:
            script = ScriptDirectory.from_config(self.config)
            versions_dir = script.versions

            if not os.path.exists(versions_dir):
                return []

            # Get all migration files
            migration_files = []
            for filename in os.listdir(versions_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    filepath = os.path.join(versions_dir, filename)
                    migration_files.append(filepath)

            # Compare migrations by reading their content
            seen_contents = {}
            duplicates = []

            for filepath in migration_files:
                with open(filepath, 'r') as f:
                    content = f.read()

                    # Extract the upgrade function content for comparison
                    upgrade_match = re.search(r'def upgrade\(\).*?def downgrade\(\)', content, re.DOTALL)
                    if upgrade_match:
                        upgrade_content = upgrade_match.group(0)

                        # Normalize whitespace for comparison
                        normalized = re.sub(r'\s+', ' ', upgrade_content)

                        if normalized in seen_contents:
                            # This is a duplicate
                            duplicates.append(filepath)
                            print(f"   Duplicate detected: {os.path.basename(filepath)}")
                        else:
                            seen_contents[normalized] = filepath

            return duplicates

        except Exception as e:
            raise MigrationError(f"Failed to detect duplicates: {str(e)}")

    def remove_duplicate_migrations(self) -> int:
        """
        Automatically detect and remove duplicate migration files.

        Returns:
            Number of duplicate files removed

        Raises:
            MigrationError: If unable to remove duplicates
        """
        try:
            duplicates = self.detect_duplicate_migrations()

            if not duplicates:
                return 0

            print(f"\n🔧 Removing {len(duplicates)} duplicate migration file(s)...")
            for dup_path in duplicates:
                os.remove(dup_path)
                print(f"   Removed: {os.path.basename(dup_path)}")

            print("✓ Duplicates cleaned up\n")
            return len(duplicates)

        except Exception as e:
            raise MigrationError(f"Failed to remove duplicates: {str(e)}")

    def check_migration_sync(self) -> Dict[str, Any]:
        """
        Check if database schema is in sync with migration files.

        Returns:
            Dictionary with sync status information

        Raises:
            MigrationError: If unable to check sync status
        """
        try:
            engine = create_engine(self.connection_string)
            with engine.connect() as connection:
                # Get current migration state
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()

                # Get expected (head) revision
                script = ScriptDirectory.from_config(self.config)
                head_rev = script.get_current_head()

                # Get pending migrations
                pending = []
                if current_rev != head_rev:
                    for rev in script.iterate_revisions(head_rev, current_rev):
                        if rev.revision != current_rev:
                            pending.append({
                                "revision": rev.revision,
                                "message": rev.doc
                            })

                # Check for tables in database
                inspector = inspect(engine)
                existing_tables = inspector.get_table_names(schema=self.schema)

                return {
                    "current_revision": current_rev,
                    "head_revision": head_rev,
                    "in_sync": current_rev == head_rev,
                    "pending_migrations": pending,
                    "existing_tables": existing_tables,
                    "has_tables": len(existing_tables) > 0
                }

        except Exception as e:
            raise MigrationError(f"Failed to check migration sync: {str(e)}")

    def smart_upgrade(self, revision: str = "head", auto_stamp_on_conflict: bool = True) -> None:
        """
        Intelligently upgrade database, handling edge cases.

        This method:
        1. Detects and removes duplicate migration files
        2. If tables exist but no migrations applied, auto-stamps
        3. If duplicate table errors occur, provides guidance
        4. Otherwise performs normal upgrade

        Args:
            revision: Target revision
            auto_stamp_on_conflict: If True, automatically stamp on duplicate table errors

        Raises:
            MigrationError: If upgrade fails
        """
        try:
            # Step 1: Clean up duplicate migration files first
            print("🔍 Checking for duplicate migration files...")
            removed = self.remove_duplicate_migrations()
            if removed == 0:
                print("✓ No duplicate migration files found\n")

            # Step 2: Check current state
            sync_info = self.check_migration_sync()

            # Case 1: Tables exist but no migrations recorded
            if sync_info["has_tables"] and sync_info["current_revision"] is None:
                print("⚠️  Tables exist but no migrations are recorded in alembic_version")
                print("💡 Auto-stamping to mark existing structure as migrated...")
                self.stamp(revision)
                print("✓ Database stamped successfully")
                return

            # Case 2: Already in sync
            if sync_info["in_sync"]:
                print("✓ Database is already up to date")
                return

            # Case 3: Normal upgrade needed
            pending_count = len(sync_info["pending_migrations"])
            print(f"📦 Applying {pending_count} pending migration(s)...")
            print(f"   From: {sync_info['current_revision'] or 'base'}")
            print(f"   To:   {revision}\n")

            try:
                command.upgrade(self.config, revision)
                print("✓ Migrations applied successfully")
            except Exception as e:
                error_msg = str(e)

                # Handle duplicate table/column errors
                if "already exists" in error_msg or "DuplicateTable" in error_msg or "DuplicateColumn" in error_msg:
                    print(f"\n⚠️  Migration conflict detected: Objects already exist in database")
                    print(f"\n🔍 Analyzing conflict...")

                    # Check if there are still duplicates that weren't caught
                    remaining_dups = self.detect_duplicate_migrations()
                    if remaining_dups:
                        print(f"⚠️  Found {len(remaining_dups)} more duplicate migration file(s)")
                        print("💡 Removing them and retrying...")
                        for dup in remaining_dups:
                            os.remove(dup)
                            print(f"   Removed: {os.path.basename(dup)}")

                        # Retry upgrade after removing duplicates
                        print("\n🔄 Retrying migration...")
                        sync_info = self.check_migration_sync()
                        if not sync_info["in_sync"]:
                            command.upgrade(self.config, revision)
                            print("✓ Migrations applied successfully after cleanup")
                        else:
                            print("✓ Database is now in sync")
                        return

                    if auto_stamp_on_conflict:
                        print("\n💡 This appears to be a legitimate conflict (tables already exist)")
                        print("   Stamping the current migration to mark it as applied...\n")

                        # Get the specific failing revision
                        current = sync_info['current_revision']
                        head = sync_info['head_revision']

                        # Stamp to head to mark all as applied
                        self.stamp(head)
                        print("✓ Database stamped to current code state")
                        print("\n📝 Note: Conflicting migration was marked as applied (not executed)")
                        print("   Future migrations with new changes will work normally.\n")
                        return
                    else:
                        print(f"\nError: {error_msg}\n")
                        print("💡 This usually means:")
                        print("   1. Tables were created manually")
                        print("   2. A previous migration was partially applied")
                        print("   3. Migration files are out of sync with database\n")
                        print("🔧 Manual fixes required:")
                        print("   1. Review and remove duplicate migration files manually")
                        print("   2. Use db.stamp_migration('head') to mark all as applied")
                        print("   3. Or set auto_stamp_on_conflict=True to auto-resolve\n")
                        raise MigrationError(f"Migration conflict: {error_msg}")
                else:
                    raise

        except MigrationError:
            raise
        except Exception as e:
            raise MigrationError(f"Failed to smart upgrade: {str(e)}")
