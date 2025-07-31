import sqlite3
import json
from typing import List

class AppDatabase:
    def __init__(self, db_path: str = 'data/app.db') -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)  # Allow multi-thread access
        self.create_tables()

    def create_tables(self) -> None:
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                selections TEXT
            )
        ''')
        self.conn.commit()

    def save_profile(self, name: str, selections: List[str]) -> None:
        self.conn.execute('INSERT OR REPLACE INTO profiles (name, selections) VALUES (?, ?)', (name, json.dumps(selections)))
        self.conn.commit()

    def load_profile(self, name: str) -> List[str]:
        cursor = self.conn.execute('SELECT selections FROM profiles WHERE name = ?', (name,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else []

    def get_all_profiles(self) -> List[str]:
        cursor = self.conn.execute('SELECT name FROM profiles')
        return [row[0] for row in cursor.fetchall()]

    def delete_profile(self, name: str) -> None:
        self.conn.execute('DELETE FROM profiles WHERE name = ?', (name,))
        self.conn.commit() 