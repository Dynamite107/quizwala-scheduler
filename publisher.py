import time
import logging
from datetime import datetime
import pytz
import config
import instagram_api
import github_queue

logging.basicConfig(
    filename=config.LOGS_DIR / 'publisher.log', level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)

def run_publisher():
    local_tz = pytz.timezone(config.TIMEZONE)
    now = datetime.now(local_tz)
    queue = github_queue.load_queue()
    pending_jobs = [j for j in queue if j["status"] == "pending"]
    
    if not pending_jobs: return
    queue_modified = False

    for job in pending_jobs:
        proc_dt = datetime.fromisoformat(job["processing_time"])
        if now >= proc_dt:
            logging.info(f"Picked Job {job['job_id'][:8]}")
            job["status"] = "processing"
            github_queue.save_queue(queue)
            
            edge_url = f"https://drive.google.com/uc?export=download&id={job['drive_id']}"
            try:
                cid = instagram_api.create_container(edge_url, job["caption"], job["media_type"])
                if not instagram_api.poll_container(cid): raise TimeoutError("Polling failed.")
                
                pub_dt = datetime.fromisoformat(job["publish_time"])
                curr_time = datetime.now(local_tz)
                if pub_dt > curr_time: time.sleep((pub_dt - curr_time).total_seconds())

                media_id = instagram_api.publish_container(cid)
                logging.info(f"Published IG ID: {media_id}")
                job["status"], job["published_id"] = "published", media_id
                queue_modified = True

            except Exception as e:
                logging.error(f"Failed: {e}")
                job["retry_count"] += 1
                job["last_error"] = str(e)
                job["status"] = "failed" if job["retry_count"] >= 3 else "pending"
                queue_modified = True

    if queue_modified: github_queue.save_queue(queue)

if __name__ == "__main__": run_publisher()
