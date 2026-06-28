import json
import datetime
import time
import logging
import pytz
import config
import facebook_api
import instagram_api
import caption
import github_queue

logging.basicConfig(
    filename=config.LOGS_DIR / 'scheduler.log', level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_state():
    if config.STATE_FILE.exists():
        with open(config.STATE_FILE, 'r') as f: return json.load(f)
    return {}

def save_state(state):
    with open(config.STATE_FILE, 'w') as f: json.dump(state, f, indent=4)

def validate_time_str(time_str):
    if not time_str or not isinstance(time_str, str): return False
    try: datetime.datetime.strptime(time_str, "%H:%M"); return True
    except ValueError: return False

def get_unix_timestamp_for_date(target_date, time_str):
    local_tz = pytz.timezone(config.TIMEZONE)
    h, m = map(int, time_str.split(':'))
    naive_dt = datetime.datetime(target_date.year, target_date.month, target_date.day, h, m, 0)
    scheduled_time = local_tz.localize(naive_dt)
    now = datetime.datetime.now(local_tz)
    min_future = now + datetime.timedelta(minutes=20)
    return int((scheduled_time if scheduled_time >= min_future else min_future).timestamp())

def resolve_slot_timing(schedule_config, day_name, old_key, new_key):
    day_cfg = schedule_config.get(day_name, {})
    return day_cfg.get(old_key) or day_cfg.get(new_key)

def construct_upload_plan(today_date, tomorrow_date):
    t_name, tm_name = today_date.strftime('%A'), tomorrow_date.strftime('%A')
    t_str, tm_str = today_date.strftime('%d %B %Y'), tomorrow_date.strftime('%d %B %Y')
    return [
        {"part": "Part1", "file_path": config.VIDEO_1, "target_date": today_date, "day_name": t_name, "old_slot": "Part1", "new_slot": "evening", "caption_date": t_str, "caption_part": "Part-3", "media_type": "REELS", "is_image": False},
        {"part": "Image", "file_path": config.IMAGE_POST, "target_date": today_date, "day_name": t_name, "old_slot": "Image", "new_slot": "evening", "caption_date": t_str, "caption_part": None, "media_type": "IMAGE", "is_image": True},
        {"part": "Part2", "file_path": config.VIDEO_2, "target_date": tomorrow_date, "day_name": tm_name, "old_slot": "Part2", "new_slot": "morning", "caption_date": tm_str, "caption_part": "Part-1", "media_type": "REELS", "is_image": False},
        {"part": "Part3", "file_path": config.VIDEO_3, "target_date": tomorrow_date, "day_name": tm_name, "old_slot": "Part3", "new_slot": "afternoon", "caption_date": tm_str, "caption_part": "Part-2", "media_type": "REELS", "is_image": False}
    ]

def run_scheduler():
    local_tz = pytz.timezone(config.TIMEZONE)
    now = datetime.datetime.now(local_tz)
    today_date = now.date()
    tomorrow_date = today_date + datetime.timedelta(days=1)
    today_name, tomorrow_name = now.strftime('%A'), tomorrow_date.strftime('%A')
    
    print("=" * 55)
    print(f"🚀 QuizWala Scheduler v4.0 Engine Initiated")
    print("=" * 55)
    
    schedule_config = config.get_schedule_config()
    if today_name not in schedule_config or tomorrow_name not in schedule_config: return
        
    state = load_state()
    upload_plan = construct_upload_plan(today_date, tomorrow_date)
    
    for task in upload_plan:
        part, file_path, target_date = task["part"], task["file_path"], task["target_date"]
        if not file_path.exists(): continue
        time_str = resolve_slot_timing(schedule_config, task["day_name"], task["old_slot"], task["new_slot"])
        if not validate_time_str(time_str): continue
            
        if target_date == today_date and part in ["Part1", "Image"]:
            h, m = map(int, time_str.split(':'))
            if local_tz.localize(datetime.datetime(target_date.year, target_date.month, target_date.day, h, m)) <= now: continue
                
        scheduled_unix = get_unix_timestamp_for_date(target_date, time_str)
        cap_text = "" if task["is_image"] else caption.get_video_caption(task["caption_date"], task["caption_part"])
        date_key = target_date.strftime('%Y-%m-%d')
        fb_key, ig_key = f"{date_key}_{part.lower()}_facebook", f"{date_key}_{part.lower()}_instagram"
        fb_status, ig_status = "SKIPPED", "SKIPPED"
        
        print(f"\n▶️ [{target_date.strftime('%d %b')}] {part} → Slot: {time_str}")
        
        if state.get(fb_key) != "scheduled":
            try:
                post_id = facebook_api.upload_and_schedule_image(str(file_path), cap_text, scheduled_unix) if task["is_image"] else facebook_api.upload_and_schedule_video(str(file_path), cap_text, scheduled_unix)
                state[fb_key] = "scheduled"; save_state(state); fb_status = f"SUCCESS ({post_id})"
                print(f"   ✅ FB Scheduled: {post_id}")
            except Exception as e: fb_status = f"FAILED"; print(f"   ❌ FB Failed: {e}")
        else: fb_status = "ALREADY_SCHEDULED"; print("   ⏭️ FB skipped.")
            
        if state.get(ig_key) != "scheduled":
            try:
                job_id = github_queue.add_job_to_queue(part, file_path, scheduled_unix, cap_text, task["media_type"])
                state[ig_key] = "scheduled"; save_state(state); ig_status = f"QUEUED ({job_id[:8]})"
                print(f"   ✅ IG Queued: {job_id[:8]}")
            except Exception as e: ig_status = f"FAILED"; print(f"   ❌ IG Failed: {e}")
        else: ig_status = "ALREADY_SCHEDULED"; print("   ⏭️ IG skipped.")

    print("\n⏳ Pushing Queue to GitHub...")
    github_queue.sync_git_queue()
    print("\n🏁 Execution Completed.")

if __name__ == "__main__": run_scheduler()
