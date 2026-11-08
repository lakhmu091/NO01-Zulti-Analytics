import sqlite3, json
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "no01.sqlite3"

def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_date TEXT, draw_id TEXT, source TEXT,
            numbers_json TEXT NOT NULL, fingerprint TEXT UNIQUE
        )""")

def save_draws(df):
    import hashlib
    init_db()
    saved = 0
    with connect() as con:
        for _, row in df.iterrows():
            nums = row.get("numbers")
            if isinstance(nums, str):
                nums = [int(x.strip()) for x in nums.split(",")]
            nums = [int(x) for x in nums]
            if not nums or len(nums) != len(set(nums)) or min(nums) < 1:
                continue
            date = str(row.get("draw_date", ""))
            draw_id = str(row.get("draw_id", ""))
            source = str(row.get("source", "unknown"))
            fingerprint = hashlib.sha256((date + "|" + draw_id + "|" + ",".join(map(str, sorted(nums)))).encode()).hexdigest()
            try:
                con.execute("INSERT INTO draws(draw_date,draw_id,source,numbers_json,fingerprint) VALUES(?,?,?,?,?)",
                            (date, draw_id, source, json.dumps(sorted(nums)), fingerprint))
                saved += 1
            except sqlite3.IntegrityError:
                pass
    return saved

def load_draws():
    init_db()
    with connect() as con:
        df = pd.read_sql_query("SELECT draw_date,draw_id,source,numbers_json FROM draws ORDER BY draw_date,id", con)
    if df.empty:
        return pd.DataFrame(columns=["draw_date","draw_id","source","numbers"])
    df["numbers"] = df["numbers_json"].apply(json.loads)
    return df.drop(columns=["numbers_json"])
