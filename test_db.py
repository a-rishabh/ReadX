# test_db.py
from dotenv import load_dotenv
load_dotenv()

from app.storage import db

db.init_db()
print("DB connected and tables created ✅")
