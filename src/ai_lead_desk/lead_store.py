"""Persistent lead identity and conversation storage using SQLite."""

import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "data" / "lead_desk.db"
DB_PATH = Path(os.getenv("LEAD_DB_PATH", str(DEFAULT_DB)))


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _now():
    return datetime.now(timezone.utc).isoformat()


def init_db():
    """Create the lead and conversation tables if they do not exist."""
    with _connect() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                platform_user_id TEXT NOT NULL,
                name TEXT,
                awaiting_name INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(platform, platform_user_id)
            );

            CREATE TABLE IF NOT EXISTS lead_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                direction TEXT NOT NULL
                    CHECK(direction IN ('inbound', 'outbound')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_lead_messages_lead_id
            ON lead_messages(lead_id, id);
        """)


def get_or_create_lead(platform, platform_user_id):
    """Return a lead profile, creating it if this is a new platform user."""
    platform = str(platform).strip().lower()
    platform_user_id = str(platform_user_id).strip()

    if not platform or not platform_user_id:
        raise ValueError("Platform and platform user ID are required.")

    now = _now()

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO leads (
                platform, platform_user_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(platform, platform_user_id) DO NOTHING
            """,
            (platform, platform_user_id, now, now),
        )

        row = connection.execute(
            """
            SELECT * FROM leads
            WHERE platform = ? AND platform_user_id = ?
            """,
            (platform, platform_user_id),
        ).fetchone()

        return dict(row)


def update_lead_name(platform, platform_user_id, name):
    """Save a user's provided name and stop asking for it."""
    name = str(name).strip()

    if not name or len(name) > 100:
        raise ValueError("Name must contain 1 to 100 characters.")

    lead = get_or_create_lead(platform, platform_user_id)

    with _connect() as connection:
        connection.execute(
            """
            UPDATE leads
            SET name = ?, awaiting_name = 0, updated_at = ?
            WHERE id = ?
            """,
            (name, _now(), lead["id"]),
        )

    return get_or_create_lead(platform, platform_user_id)


def set_awaiting_name(platform, platform_user_id, awaiting=True):
    """Record whether the bot is waiting for the user's name."""
    lead = get_or_create_lead(platform, platform_user_id)

    with _connect() as connection:
        connection.execute(
            """
            UPDATE leads
            SET awaiting_name = ?, updated_at = ?
            WHERE id = ?
            """,
            (int(bool(awaiting)), _now(), lead["id"]),
        )

    return get_or_create_lead(platform, platform_user_id)


def add_message(platform, platform_user_id, direction, content):
    """Save an inbound or outbound message against the user's lead."""
    direction = str(direction).strip().lower()
    content = str(content).strip()

    if direction not in {"inbound", "outbound"}:
        raise ValueError("Direction must be inbound or outbound.")

    if not content:
        raise ValueError("Message content cannot be empty.")

    lead = get_or_create_lead(platform, platform_user_id)

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO lead_messages (
                lead_id, direction, content, created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (lead["id"], direction, content, _now()),
        )
        connection.execute(
            "UPDATE leads SET updated_at = ? WHERE id = ?",
            (_now(), lead["id"]),
        )


def get_recent_messages(platform, platform_user_id, limit=20):
    """Return recent conversation messages in chronological order."""
    lead = get_or_create_lead(platform, platform_user_id)
    limit = max(1, min(int(limit), 100))

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT direction, content, created_at
            FROM lead_messages
            WHERE lead_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (lead["id"], limit),
        ).fetchall()

    return [dict(row) for row in reversed(rows)]


init_db()
