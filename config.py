import os
from dotenv import load_dotenv

load_dotenv()

# Leer variables del archivo .env
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is required for MongoDB Atlas connection")

DB_NAME = os.getenv("DB_NAME", "exam_system")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")

EXAM_TIME = int(os.getenv("EXAM_TIME", 1800))
MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", 3))