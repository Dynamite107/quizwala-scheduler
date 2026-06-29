import json
import os
from datetime import datetime
import pytz
import config
import instagram_api

def load_queue():
    if config.QUEUE_FILE.exists():
        with open(config.QUEUE_FILE, "r") as f:
            try: return json.load(f)
            except: return []
    return []

def save_queue(queue_data):
    with open(config.QUEUE_FILE, "w") as f:
        json.dump(queue_data, f, indent=4)
    print("💾 [LOG] Queue state committed to disk.")

def run_state_machine():
    queue = load_queue()
    tz = pytz.timezone(config.TIMEZONE)
    now = datetime.now(tz)
    action_taken = False

    for job in queue:
        # Auto-heal missing keys for backward compatibility
        job.setdefault("container_id", "")
        job.setdefault("published_id", "")
        job.setdefault("status", "pending")
        job.setdefault("retry_count", 0)
        job.setdefault("last_error", "")

        if job["status"] in ["published", "FAILED"]:
            continue

        try:
            proc_dt = datetime.fromisoformat(job["processing_time"])
            pub_dt = datetime.fromisoformat(job["publish_time"])
        except Exception: continue

        try:
            # STAGE A: PENDING -> CREATE CONTAINER
            if job["status"] == "pending" and now >= proc_dt:
                print(f"▶️ [{job['part_name']}] Triggering Meta Container Creation...")
                edge_url = f"https://drive.google.com/uc?export=download&id={job['drive_id']}"
                
                cid = instagram_api.create_container(edge_url, job["caption"], job.get("media_type", "REELS"))
                job["container_id"] = cid
                job["status"] = "container_created"
                job["retry_count"] = 0
                action_taken = True
                print(f"   ✅ Created CID: {cid}")
                save_queue(queue)

            # STAGE B: CONTAINER_CREATED -> POLL
            elif job["status"] == "container_created":
                print(f"🔎 [{job['part_name']}] Checking container {job['container_id']} status...")
                if instagram_api.poll_container(job["container_id"]):
                    job["status"] = "container_ready"
                    job["retry_count"] = 0
                    action_taken = True
                    print(f"   ✅ Container is READY for launch!")
                    save_queue(queue)
                else:
                    print("   ⏳ Still IN_PROGRESS. Quitting workflow run.")

            # STAGE C: CONTAINER_READY -> PUBLISH
            elif job["status"] == "container_ready" and now >= pub_dt:
                print(f"🔥 [{job['part_name']}] FIRING PUBLISH TRIGGER TO META...")
                pid = instagram_api.publish_container(job["container_id"])
                
                job["published_id"] = pid
                job["status"] = "published"
                job["retry_count"] = 0
                action_taken = True
                print(f"   👑 SUCCESS! Published Post ID: {pid}")
                save_queue(queue)

        except Exception as e:
            job["retry_count"] += 1
            job["last_error"] = str(e)
            action_taken = True
            print(f"   ❌ Stage Error ({job['status']}) -> {e} [Retry {job['retry_count']}/3]")
            if job["retry_count"] >= 3:
                job["status"] = "FAILED"
                print(f"   💀 Job marked permanently FAILED.")
            save_queue(queue)

    if not action_taken:
        print("💤 [LOG] All jobs in idle state. Exiting cleanly.")

if __name__ == "__main__": run_state_machine()
