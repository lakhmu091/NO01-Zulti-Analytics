import sqlite3, json, hashlib
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "no01.sqlite3"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        con.execute('''CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_date TEXT NOT NULL, draw_id TEXT DEFAULT '',
            source TEXT DEFAULT 'Manual', numbers_json TEXT NOT NULL,
            fingerprint TEXT UNIQUE NOT NULL)''')

def save_draw(draw_date, draw_id, numbers, source="Manual"):
    nums = sorted(int(n) for n in numbers)
    if len(nums) != 6 or len(set(nums)) != 6 or min(nums) < 1 or max(nums) > 45:
        return False, "Expected six unique numbers in range 1–45."
    payload = json.dumps(nums)
    fingerprint = hashlib.sha256(f"{draw_date}|{draw_id}|{payload}".encode()).hexdigest()
    try:
        with sqlite3.connect(DB_PATH) as con:
            con.execute("INSERT INTO draws(draw_date,draw_id,source,numbers_json,fingerprint) VALUES(?,?,?,?,?)",
                        (draw_date, draw_id, source, payload, fingerprint))
        return True, "Saved"
    except sqlite3.IntegrityError:
        return False, "Duplicate"

def load_draws():
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("SELECT draw_date,draw_id,source,numbers_json FROM draws ORDER BY draw_date DESC,id DESC").fetchall()
    return pd.DataFrame([{"draw_date": r[0], "draw_id": r[1], "source": r[2],
                          "numbers": " ".join(map(str, json.loads(r[3])))} for r in rows],
                        columns=["draw_date", "draw_id", "source", "numbers"])
