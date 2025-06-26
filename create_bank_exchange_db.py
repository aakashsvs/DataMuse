import sqlite3
import pandas as pd
import os

DB_PATH = "business.db"
DATA_FOLDER = "data"

def create_db_from_excels():
    # Remove old DB if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑️ Deleted existing database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for file in os.listdir(DATA_FOLDER):
        if file.endswith(".xlsx"):
            table_name = os.path.splitext(file)[0]
            df = pd.read_excel(os.path.join(DATA_FOLDER, file))
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            print(f"✅ Loaded: {file} → table '{table_name}'")

    conn.commit()
    conn.close()
    print("🎉 All Excel files loaded into new business.db")

if __name__ == "__main__":
    create_db_from_excels()
