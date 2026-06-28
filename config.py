import os
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path("/content/drive/MyDrive/QuizEngine_IG_GPU")
SCHEDULER_DIR = BASE_DIR / "Scheduler"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = SCHEDULER_DIR / "logs"
TEMP_DIR = SCHEDULER_DIR / "temp"

ENV_FILE = BASE_DIR / ".env"
STATE_FILE = SCHEDULER_DIR / "state.json"
SCHEDULE_CONFIG_FILE = SCHEDULER_DIR / "schedule_config.json"
DRIVE_CACHE_FILE = TEMP_DIR / "drive_cache.json"

VIDEO_1 = OUTPUT_DIR / "Video_Part_1.mp4"
VIDEO_2 = OUTPUT_DIR / "Video_Part_2.mp4"
VIDEO_3 = OUTPUT_DIR / "Video_Part_3.mp4"
IMAGE_POST = OUTPUT_DIR / "final_daily_post.png"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    print(f"⚠️ WARNING: .env file not found at {ENV_FILE}")

# STRICT SPECS FIX: Support for META_ prefixed keys
APP_ID = os.getenv("APP_ID") or os.getenv("META_APP_ID")
APP_SECRET = os.getenv("APP_SECRET") or os.getenv("META_APP_SECRET")
PAGE_ID = os.getenv("PAGE_ID") or os.getenv("FB_PAGE_ID")
IG_USER_ID = os.getenv("IG_USER_ID") or os.getenv("INSTAGRAM_ID")
USER_ACCESS_TOKEN = os.getenv("USER_ACCESS_TOKEN") or os.getenv("IG_ACCESS_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN") or os.getenv("FB_PAGE_ACCESS_TOKEN")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

def get_schedule_config():
    if not SCHEDULE_CONFIG_FILE.exists():
        raise FileNotFoundError(f"Schedule config missing at {SCHEDULE_CONFIG_FILE}")
    with open(SCHEDULE_CONFIG_FILE, 'r') as file:
        return json.load(file)

def validate_environment():
    missing = []
    if not APP_ID: missing.append("APP_ID")
    if not APP_SECRET: missing.append("APP_SECRET")
    if not PAGE_ID: missing.append("PAGE_ID")
    if not IG_USER_ID: missing.append("IG_USER_ID")
    if not USER_ACCESS_TOKEN: missing.append("USER_ACCESS_TOKEN")
    if not PAGE_ACCESS_TOKEN: missing.append("PAGE_ACCESS_TOKEN")
    
    if missing:
        raise ValueError(f"Missing essential variables in .env: {', '.join(missing)}")
    print("✅ Configuration & Meta Credentials Validated Successfully!")


