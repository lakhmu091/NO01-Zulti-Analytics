import argparse
import pandas as pd
from database import init_db, save_draw

def import_csv(path):
    init_db()
    df = pd.read_csv(path)
    if not {"draw_date","numbers"}.issubset(df.columns):
        raise ValueError("CSV requires draw_date and numbers.")
    added = skipped = 0
    for _, row in df.iterrows():
        nums = [int(x) for x in str(row["numbers"]).replace(",", " ").split()]
        ok, _ = save_draw(str(row["draw_date"]), str(row.get("draw_id","")), nums, "CSV")
        added += int(ok)
        skipped += int(not ok)
    return added, skipped

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    args = parser.parse_args()
    print("Imported:", import_csv(args.csv_file))
