import time
import config
import meta_auth

GRAPH = "v25.0"
BASE = f"https://graph.facebook.com/{GRAPH}"

def create_container(edge_url: str, caption: str, media_type="REELS") -> str:
    url = f"{BASE}/{config.IG_USER_ID}/media"
    payload = meta_auth.get_auth_payload(is_page=True)
    payload['caption'] = caption

    if media_type == "REELS":
        payload['media_type'] = 'REELS'
        payload['video_url'] = edge_url
    else:
        payload['image_url'] = edge_url

    session = meta_auth.get_secure_session()
    resp = session.post(url, data=payload)
    if not resp.ok:
        raise Exception(f"Container Creation Failed: {resp.text}")
    return resp.json()['id']

def poll_container(cid: str) -> bool:
    session = meta_auth.get_secure_session()
    payload = meta_auth.get_auth_payload(is_page=True)
    
    for _ in range(config.MAX_POLL):
        time.sleep(config.POLL_INTERVAL)
        res = session.get(f"{BASE}/{cid}", params={
            "fields": "status_code",
            "access_token": payload['access_token']
        }).json()
        status = res.get('status_code', 'UNKNOWN')
        if status == "FINISHED": return True
        if status == "ERROR": raise Exception(f"Meta IG Container Failed: {res}")
    return False

def publish_container(cid: str) -> str:
    session = meta_auth.get_secure_session()
    payload = meta_auth.get_auth_payload(is_page=True)
    pub_resp = session.post(f"{BASE}/{config.IG_USER_ID}/media_publish", data={
        "creation_id": cid, "access_token": payload['access_token']
    }).json()
    if "id" not in pub_resp: raise Exception(f"Publish Trigger Failed: {pub_resp}")
    return pub_resp['id']
