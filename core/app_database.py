"""Database module for managing application profiles and data."""

import sqlite3
import json
from typing import List


class AppDatabase:
    """Database class for managing application profiles using SQLite."""

    def __init__(self, db_path: str = "data/app.db") -> None:
        """Initialize the database connection and create necessary tables.

        Args:
            db_path: Path to the SQLite database file
        """
        self.conn = sqlite3.connect(db_path, check_same_thread=False)  # Allow multi-thread access
        self.create_tables()

    def create_tables(self) -> None:
        """Create necessary database tables if they don't exist."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                selections TEXT
            )
        """
        )
        self.conn.commit()

    def save_profile(self, name: str, selections: List[str]) -> None:
        """Save a profile with selected package IDs.

        Args:
            name: Profile name
            selections: List of selected package IDs
        """
        self.conn.execute(
            "INSERT OR REPLACE INTO profiles (name, selections) VALUES (?, ?)",
            (name, json.dumps(selections)),
        )
        self.conn.commit()

    def load_profile(self, name: str) -> List[str]:
        """Load a saved profile by name.

        Args:
            name: Profile name to load

        Returns:
            List of package IDs in the profile
        """
        cursor = self.conn.execute("SELECT selections FROM profiles WHERE name = ?", (name,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else []

    def get_all_profiles(self) -> List[str]:
        """Get all saved profile names.

        Returns:
            List of profile names
        """
        cursor = self.conn.execute("SELECT name FROM profiles")
        return [row[0] for row in cursor.fetchall()]

    def delete_profile(self, name: str) -> None:
        """Delete a profile by name.

        Args:
            name: Profile name to delete
        """
        self.conn.execute("DELETE FROM profiles WHERE name = ?", (name,))
        self.conn.commit()
