import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

project = Path(__file__).resolve().parent
sys.path.insert(0, str(project / "src"))

from ai_lead_desk import lead_store

if os.environ.get("CONFIRM_CHAT_RESET") != "DELETE ALL CHATS":
    raise SystemExit("Confirmation missing. Nothing deleted.")

db = Path(lead_store.DB_PATH).resolve()

if not db.is_file():
    raise SystemExit(f"Database not found: {db}")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
backup = db.with_name(f"{db.stem}.backup_chats_{stamp}{db.suffix}")

with sqlite3.connect(str(db), timeout=30) as src:
    with sqlite3.connect(str(backup)) as dst:
        src.backup(dst)

with sqlite3.connect(str(backup)) as check:
    if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        backup.unlink(missing_ok=True)
        raise SystemExit("Backup integrity check failed. Original untouched.")

print(f"Verified backup: {backup}")

conn = sqlite3.connect(str(db), timeout=30)
conn.execute("PRAGMA foreign_keys = ON")

try:
    conn.execute("BEGIN IMMEDIATE")
    tables = {
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }

    if not {"leads", "lead_messages"}.issubset(tables):
        raise RuntimeError("Expected conversation tables are missing.")

    targets = [
        t for t in ("counselor_events", "lead_messages", "leads")
        if t in tables
    ]

    counts = {
        t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        for t in targets
    }

    for table in targets:
        conn.execute(f'DELETE FROM "{table}"')

    for table in targets:
        remaining = conn.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]
        if remaining:
            raise RuntimeError(f"Rows remain in {table}: {remaining}")

    if conn.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("Database foreign-key check failed.")

    conn.commit()

    print("\nDeleted local records:")
    for table, count in counts.items():
        print(f"  {table}: {count}")

    print("\nSUCCESS: Conversation history cleared.")
    print("Telegram messages themselves were not deleted.")

except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
