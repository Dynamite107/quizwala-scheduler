import os
import json
from pathlib import Path
from dotenv import load_dotenv
import pytz

# ==========================================
# 1. PATH DIRECTORY MANAGEMENT
# ==========================================
if os.getenv("GITHUB_ACTIONS") == "true":
    BASE_DIR = Path(__file__).resolve().parent
    SCHEDULER_DIR = BASE_DIR
    OUTPUT_DIR = BASE_DIR / "output"
    ENV_PATH = SCHEDULER_DIR / ".env"
else:
    BASE_DIR = Path("/content/drive/MyDrive/QuizEngine_IG_GPU")
    SCHEDULER_DIR = BASE_DIR / "Scheduler"
    OUTPUT_DIR = BASE_DIR / "output"
    ENV_PATH = SCHEDULER_DIR / ".env"

load_dotenv(ENV_PATH)

# ==========================================
# 2. TIMEZONE & ENGINE ANCHORS
# ==========================================
TZ = pytz.timezone("Asia/Kolkata")
TIMEZONE = "Asia/Kolkata"

PUBLISH_BUFFER_MINUTES = 5
MAX_POLL = 30
POLL_INTERVAL = 10

# ==========================================
# 3. FILE & DIRECTORY PATHS (POINT 3 & 7 FIX)
# ==========================================
QUEUE_FILE = SCHEDULER_DIR / "queue.json"
STATE_FILE = SCHEDULER_DIR / "state.json"
SCHEDULE_CONFIG_FILE = SCHEDULER_DIR / "schedule_config.json"

LOGS_DIR = SCHEDULER_DIR / "logs"
TEMP_DIR = SCHEDULER_DIR / "temp"

# Auto-Create system folders
LOGS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DRIVE_CACHE_FILE = TEMP_DIR / "drive_cache.json"

# ==========================================
# 4. MEDIA ASSETS MAPPING (POINT 2 FIX)
# ==========================================
VIDEO_1 = OUTPUT_DIR / "Video_Part_1.mp4"
VIDEO_2 = OUTPUT_DIR / "Video_Part_2.mp4"
VIDEO_3 = OUTPUT_DIR / "Video_Part_3.mp4"
IMAGE_POST = OUTPUT_DIR / "final_daily_post.png"

# ==========================================
# 5. META CREDENTIALS & ALIASES (POINT 1 FIX)
# ==========================================
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
USER_ACCESS_TOKEN = os.getenv("USER_ACCESS_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")
IG_USER_ID = os.getenv("IG_USER_ID")
GITHUB_TOKEN = os.getenv("Github_Token")

# Backward Compatibility Aliases (Taaki koi purana module na phate)
FB_PAGE_ID = PAGE_ID
FB_ACCESS_TOKEN = PAGE_ACCESS_TOKEN
IG_ACCESS_TOKEN = USER_ACCESS_TOKEN

# ==========================================
# 6. CORE ARCHITECTURAL METHODS (POINT 6 FIX)
# ==========================================
def validate_environment():
    required_keys = {
        "APP_ID": APP_ID,
        "APP_SECRET": APP_SECRET,
        "USER_ACCESS_TOKEN": USER_ACCESS_TOKEN,
        "PAGE_ACCESS_TOKEN": PAGE_ACCESS_TOKEN,
        "PAGE_ID": PAGE_ID,
        "IG_USER_ID": IG_USER_ID
    }
    missing = [name for name, val in required_keys.items() if not val]
    if missing:
        raise ValueError(f"CRITICAL: Missing environment credentials in .env -> {', '.join(missing)}")
    return True

def get_schedule_config():
    if not SCHEDULE_CONFIG_FILE.exists():
        return {}
    with open(SCHEDULE_CONFIG_FILE, "r") as f:
        return json.load(f)
