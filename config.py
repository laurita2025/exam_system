import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("DB_NAME", "exam_system")
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecret")
EXAM_TIME = int(os.environ.get("EXAM_TIME", 1800))
MAX_WARNINGS = int(os.environ.get("MAX_WARNINGS", 3))
