import json
import uuid
import subprocess
from datetime import datetime, timedelta
import pytz
import config

def _get_drive_id(file_path):
    fname = file_path.name
    if not config.DRIVE_CACHE_FILE.exists():
        raise FileNotFoundError(f"Drive cache missing at {config.DRIVE_CACHE_FILE}")
    with open(config.DRIVE_CACHE_FILE, "r") as f:
        cache = json.load(f)
    drive_id = cache.get(fname)
    if not drive_id: raise ValueError(f"Missing Drive ID for {fname}")
    return drive_id

def load_queue():
    if config.QUEUE_FILE.exists():
        with open(config.QUEUE_FILE, "r") as f:
            try: return json.load(f)
            except: return []
    return []

def save_queue(queue_data):
    with open(config.QUEUE_FILE, "w") as f:
        json.dump(queue_data, f, indent=4)

def add_job_to_queue(part, file_path, scheduled_unix, caption, media_type):
    queue = load_queue()
    drive_id = _get_drive_id(file_path)
    local_tz = pytz.timezone(config.TIMEZONE)
    
    pub_dt = datetime.fromtimestamp(scheduled_unix, local_tz)
    proc_dt = pub_dt - timedelta(minutes=config.PUBLISH_BUFFER_MINUTES)
    pub_iso, proc_iso = pub_dt.isoformat(), proc_dt.isoformat()
    
    for job in queue:
        if job.get("drive_id") == drive_id and job.get("publish_time") == pub_iso:
            return job["job_id"]

    new_job = {
        "job_id": str(uuid.uuid4()), 
        "part_name": part, 
        "status": "pending",
        "retry_count": 0, 
        "container_id": "",
        "published_id": "",
        "last_error": "",
        "media_type": media_type, 
        "drive_id": drive_id,
        "caption": caption, 
        "publish_time": pub_iso, 
        "processing_time": proc_iso
    }
    queue.append(new_job)
    save_queue(queue)
    return new_job["job_id"]

def sync_git_queue():
    try:
        subprocess.run(["git", "add", "queue.json"], check=True, cwd=config.SCHEDULER_DIR)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=config.SCHEDULER_DIR)
        if "queue.json" in status.stdout:
            subprocess.run(["git", "commit", "-m", "chore(queue): update IG schedule [skip ci]"], check=True, cwd=config.SCHEDULER_DIR)
            subprocess.run(["git", "push"], check=True, cwd=config.SCHEDULER_DIR)
            print("   🚀 queue.json successfully pushed to GitHub!")
        else: print("   ℹ️ Git Queue unchanged.")
    except Exception as e:
        print(f"   ⚠️ Git Auto-Push Warning: {e}. Push manually if needed!")
