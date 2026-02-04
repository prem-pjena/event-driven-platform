import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

print("🚨 DATABASE_URL USED BY APP:", DATABASE_URL)
