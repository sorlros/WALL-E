import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE detections ADD COLUMN is_manual BOOLEAN DEFAULT FALSE;"))
        conn.commit()
        print("Column 'is_manual' added successfully!")
    except Exception as e:
        print(f"Error adding column (it may already exist): {e}")

    try:
        # Also update schema.sql for future reference
        with open("db/schema.sql", "r") as f:
            content = f.read()
        
        if "is_manual" not in content:
            content = content.replace(
                "label text,",
                "label text,\n  is_manual boolean default false,"
            )
            with open("db/schema.sql", "w") as f:
                f.write(content)
            print("schema.sql updated successfully!")
    except Exception as e:
        print(f"Error updating schema.sql: {e}")
