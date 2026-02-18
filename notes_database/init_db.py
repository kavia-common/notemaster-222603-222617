#!/usr/bin/env python3
"""Initialize SQLite database for notes_database.

This container owns the SQLite file. The backend connects to it via the SQLITE_DB
environment variable (path to the .db file).

This script is safe to run multiple times; it uses IF NOT EXISTS and idempotent
seed operations.
"""

import os
import sqlite3

DB_NAME = os.environ.get("SQLITE_DB", "myapp.db")

print("Starting SQLite setup...")
print(f"DB file: {DB_NAME}")

# Ensure directory exists if SQLITE_DB is a path like /data/myapp.db
db_dir = os.path.dirname(os.path.abspath(DB_NAME))
os.makedirs(db_dir, exist_ok=True)

# Connect and create schema
conn = sqlite3.connect(DB_NAME)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

# Meta table (kept from template)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS app_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)

# Notes core
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL DEFAULT '',
        content TEXT NOT NULL DEFAULT '',
        is_pinned INTEGER NOT NULL DEFAULT 0,
        is_favorite INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
"""
)

# Tags and many-to-many mapping
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS note_tags (
        note_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (note_id, tag_id),
        FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
    )
"""
)

# Indexes for search/filter/sort
cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(is_pinned)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_favorite ON notes(is_favorite)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_tags_note ON note_tags(note_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_tags_tag ON note_tags(tag_id)")

# Seed app_info (idempotent)
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("project_name", "notes_database"),
)
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("version", "0.1.0"),
)
cursor.execute(
    "INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)",
    ("description", "SQLite storage for Notemaster notes/tags."),
)

conn.commit()

# Save connection information to a file (used by agents / operators)
current_dir = os.getcwd()
abs_db_path = os.path.abspath(DB_NAME)
connection_string = f"sqlite:///{abs_db_path}"

try:
    with open("db_connection.txt", "w", encoding="utf-8") as f:
        f.write("# SQLite connection methods:\n")
        f.write(f"# Python: sqlite3.connect('{DB_NAME}')\n")
        f.write(f"# Connection string: {connection_string}\n")
        f.write(f"# File path: {abs_db_path}\n")
    print("Connection information saved to db_connection.txt")
except Exception as e:
    print(f"Warning: Could not save connection info: {e}")

conn.close()

print("\nSQLite setup complete!")
print(f"Database file: {abs_db_path}")
print("Script completed successfully.")
