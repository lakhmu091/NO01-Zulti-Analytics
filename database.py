
import sqlite3
import json
import hashlib
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "no01.sqlite3"

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draw_date TEXT,
                draw_id TEXT,
                source TEXT,
                numbers_json TEXT NOT NULL,
                fingerprint TEXT UNIQUE
            )
        """)

def save_draws(df):
    init_db()
    saved = 0

    with connect() as con:
        for _, row in df.iterrows():
            try:
                nums = row.get("numbers")

                if isinstance(nums, str):
                    nums = [int(x.strip()) for x in nums.split(",")]
                elif isinstance(nums, (list, tuple)):
                    nums = [int(x) for x in nums]
                else:
                    continue

                # Exactly 8 unique positive numbers
                if len(nums) != 8:
                    continue

                if len(nums) != len(set(nums)):
                    continue

                if min(nums) < 1 or max(nums) > 100:
                    continue

                date = str(row.get("draw_date", ""))
                draw_id = str(row.get("draw_id", ""))
                source = str(row.get("source", "unknown"))

                fingerprint = hashlib.sha256(
                    (date + "|" + draw_id + "|" +
                     ",".join(map(str, sorted(nums)))).encode()
                ).hexdigest()

                con.execute("""
                    INSERT OR IGNORE INTO draws
                    (draw_date, draw_id, source, numbers_json, fingerprint)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    date, draw_id, source,
                    json.dumps(sorted(nums)), fingerprint
                ))

                saved += con.execute(
                    "SELECT changes()"
                ).fetchone()[0]

            except (ValueError, TypeError):
                continue

    return saved

def load_draws():
    init_db()

    with connect() as con:
        df = pd.read_sql_query(
            """SELECT draw_date, draw_id, source, numbers_json
               FROM draws ORDER BY draw_date, id""",
            con
        )

    if df.empty:
        return pd.DataFrame(
            columns=["draw_date", "draw_id", "source", "numbers"]
        )

    df["numbers"] = df["numbers_json"].apply(json.loads)

    return df.drop(columns=["numbers_json"])
