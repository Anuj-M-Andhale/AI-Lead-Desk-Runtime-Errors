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

        # Additive migration: preserve every existing lead and message.
        lead_columns = {
            row[1] for row in
            connection.execute("PRAGMA table_info(leads)").fetchall()
        }

        lead_additions = {
            "chat_id": "TEXT",
            "handling_mode": "TEXT NOT NULL DEFAULT 'ai'",
            "assigned_counselor": "TEXT",
            "last_counselor_viewed_message_id":
                "INTEGER NOT NULL DEFAULT 0",
        }

        for column, definition in lead_additions.items():
            if column not in lead_columns:
                connection.execute(
                    f"ALTER TABLE leads ADD COLUMN {column} {definition}"
                )

        message_columns = {
            row[1] for row in
            connection.execute("PRAGMA table_info(lead_messages)").fetchall()
        }

        if "sender_type" not in message_columns:
            connection.execute(
                "ALTER TABLE lead_messages "
                "ADD COLUMN sender_type TEXT NOT NULL DEFAULT 'ai'"
            )

            # Existing inbound records were written by the student.
            connection.execute(
                "UPDATE lead_messages SET sender_type = 'student' "
                "WHERE direction = 'inbound'"
            )

        connection.executescript("""
            CREATE TABLE IF NOT EXISTS counselor_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL DEFAULT 'system',
                details TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_counselor_events_lead_id
            ON counselor_events(lead_id, id);
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


def add_message(platform, platform_user_id, direction, content, sender_type=None):
    """Save an inbound or outbound message against the user's lead."""
    direction = str(direction).strip().lower()
    content = str(content).strip()

    if direction not in {"inbound", "outbound"}:
        raise ValueError("Direction must be inbound or outbound.")

    sender_type = str(
        sender_type or ("student" if direction == "inbound" else "ai")
    ).strip().lower()

    if sender_type not in {"student", "ai", "counselor", "system"}:
        raise ValueError(
            "sender_type must be student, ai, counselor, or system."
        )

    if not content:
        raise ValueError("Message content cannot be empty.")

    lead = get_or_create_lead(platform, platform_user_id)

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO lead_messages (
                lead_id, direction, content, created_at, sender_type
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (lead["id"], direction, content, _now(), sender_type),
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
            SELECT direction, content, created_at, sender_type
            FROM lead_messages
            WHERE lead_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (lead["id"], limit),
        ).fetchall()

    return [dict(row) for row in reversed(rows)]


init_db()



# =========================================================
# COUNSELOR INBOX AND HUMAN TAKEOVER
# =========================================================

def set_platform_chat_id(platform, platform_user_id, chat_id):
    """Persist the destination used for replying on a messaging platform."""
    platform = str(platform).strip().lower()
    platform_user_id = str(platform_user_id).strip()
    chat_id = str(chat_id).strip()

    if not chat_id:
        raise ValueError("A platform chat ID is required.")

    lead = get_or_create_lead(platform, platform_user_id)

    with _connect() as connection:
        connection.execute(
            "UPDATE leads SET chat_id = ?, updated_at = ? WHERE id = ?",
            (chat_id, _now(), lead["id"]),
        )

    return get_or_create_lead(platform, platform_user_id)


def get_handling_mode(platform, platform_user_id):
    """Return the persistent handling mode for one conversation."""
    lead = get_or_create_lead(platform, platform_user_id)
    return lead.get("handling_mode") or "ai"


def set_handling_mode(
    platform,
    platform_user_id,
    mode,
    actor="counselor",
):
    """Switch AI/human ownership and record a counselor audit event."""
    platform = str(platform).strip().lower()
    platform_user_id = str(platform_user_id).strip()
    mode = str(mode).strip().lower()
    actor = str(actor or "counselor").strip()[:100] or "counselor"

    if mode not in {"ai", "human"}:
        raise ValueError("mode must be 'ai' or 'human'.")

    lead = get_or_create_lead(platform, platform_user_id)
    event_type = "takeover" if mode == "human" else "resume_ai"

    with _connect() as connection:
        connection.execute(
            """
            UPDATE leads
            SET handling_mode = ?,
                assigned_counselor = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                mode,
                actor if mode == "human" else None,
                _now(),
                lead["id"],
            ),
        )

        connection.execute(
            """
            INSERT INTO counselor_events (
                lead_id, event_type, actor, details, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                lead["id"],
                event_type,
                actor,
                f"handling_mode={mode}",
                _now(),
            ),
        )

    return get_or_create_lead(platform, platform_user_id)


def list_conversations(limit=100, platform=None):
    """Return inbox summaries with last message, unread count, and mode."""
    init_db()
    limit = max(1, min(int(limit), 500))

    query = """
        SELECT
            l.id AS lead_id,
            l.platform,
            l.platform_user_id,
            l.chat_id,
            l.name,
            l.handling_mode,
            l.assigned_counselor,
            l.created_at,
            l.updated_at,
            COUNT(m.id) AS message_count,
            COALESCE(
                SUM(
                    CASE
                        WHEN m.direction = 'inbound'
                        AND m.id > l.last_counselor_viewed_message_id
                        THEN 1 ELSE 0
                    END
                ), 0
            ) AS unread_count,
            (
                SELECT content FROM lead_messages
                WHERE lead_id = l.id
                ORDER BY id DESC LIMIT 1
            ) AS last_message,
            (
                SELECT direction FROM lead_messages
                WHERE lead_id = l.id
                ORDER BY id DESC LIMIT 1
            ) AS last_message_direction,
            (
                SELECT created_at FROM lead_messages
                WHERE lead_id = l.id
                ORDER BY id DESC LIMIT 1
            ) AS last_message_at,
            (
                SELECT COALESCE(MAX(id), 0) FROM lead_messages
                WHERE lead_id = l.id
            ) AS latest_message_id
        FROM leads l
        LEFT JOIN lead_messages m ON m.lead_id = l.id
    """

    params = []

    if platform:
        query += " WHERE lower(l.platform) = ?"
        params.append(str(platform).strip().lower())

    query += """
        GROUP BY l.id
        ORDER BY l.updated_at DESC, l.id DESC
        LIMIT ?
    """
    params.append(limit)

    with _connect() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def mark_conversation_read(platform, platform_user_id):
    """Mark all messages currently in a conversation as seen by a counselor."""
    lead = get_or_create_lead(platform, platform_user_id)

    with _connect() as connection:
        latest = connection.execute(
            "SELECT COALESCE(MAX(id), 0) FROM lead_messages WHERE lead_id = ?",
            (lead["id"],),
        ).fetchone()[0]

        connection.execute(
            """
            UPDATE leads
            SET last_counselor_viewed_message_id = ?
            WHERE id = ?
            """,
            (latest, lead["id"]),
        )

    return latest


def get_counselor_events(platform, platform_user_id, limit=100):
    """Return the audit trail for a conversation."""
    limit = max(1, min(int(limit), 500))

    lead = get_or_create_lead(platform, platform_user_id)

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT event_type, actor, details, created_at
            FROM counselor_events
            WHERE lead_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (lead["id"], limit),
        ).fetchall()

    return [dict(row) for row in reversed(rows)]


# Apply any pending additive migrations when this module is imported.
init_db()
