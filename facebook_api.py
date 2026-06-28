import os
import config
import meta_auth

GRAPH_API_VERSION = "v25.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Default chunk size — Facebook khud bhi 'end_offset' return karta hai jo
# actual chunk boundaries decide karta hai, ye sirf fallback hai.
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024  # 4MB


def _start_upload_session(file_path, session):
    """
    PHASE 1: START
    Returns: (upload_session_id, video_id, start_offset, end_offset)
    """
    file_size = os.path.getsize(file_path)
    payload = meta_auth.get_auth_payload(is_page=True)
    payload.update({
        "upload_phase": "start",
        "file_size": file_size,
    })

    response = session.post(f"{BASE_URL}/{config.PAGE_ID}/videos", data=payload)
    if not response.ok:
        raise Exception(f"Start Phase Error: {response.text}")

    result = response.json()
    upload_session_id = result.get("upload_session_id")
    video_id = result.get("video_id")
    start_offset = int(result.get("start_offset", 0))
    end_offset = int(result.get("end_offset", 0))

    if not upload_session_id or not video_id:
        raise Exception(f"Start Phase Incomplete Response: {result}")

    return upload_session_id, video_id, start_offset, end_offset, file_size


def _transfer_chunks(file_path, upload_session_id, start_offset, end_offset, file_size, session):
    """
    PHASE 2: TRANSFER (loop)
    Video ko Facebook ke diye gaye offset boundaries ke hisaab se chunks me
    bhejta hai. retry_post=False session use hota hai (caller se aata hai)
    taaki duplicate/corrupted bytes na bhej jaayein.
    """
    current_offset = start_offset

    with open(file_path, "rb") as f:
        while current_offset < file_size:
            chunk_len = (end_offset - current_offset) if end_offset > current_offset else DEFAULT_CHUNK_SIZE
            f.seek(current_offset)
            chunk_data = f.read(chunk_len)

            if not chunk_data:
                raise Exception(f"Transfer Phase: No data read at offset {current_offset}")

            payload = meta_auth.get_auth_payload(is_page=True)
            payload.update({
                "upload_phase": "transfer",
                "upload_session_id": upload_session_id,
                "start_offset": str(current_offset),
            })
            files = {"video_file_chunk": chunk_data}

            response = session.post(f"{BASE_URL}/{config.PAGE_ID}/videos", data=payload, files=files)
            if not response.ok:
                raise Exception(f"Transfer Phase Error at offset {current_offset}: {response.text}")

            result = response.json()
            new_offset = int(result.get("start_offset", current_offset))
            new_end = int(result.get("end_offset", new_offset))

            # Safety check: offset aage nahi badha aur file abhi complete nahi hui -> stuck loop se bachao
            if new_offset <= current_offset and new_offset < file_size:
                raise Exception(f"Transfer Phase Stuck: offset did not advance past {new_offset}. Response: {result}")

            current_offset = new_offset
            end_offset = new_end


def _finish_upload(upload_session_id, video_id, caption, scheduled_time_unix, session):
    """
    PHASE 3: FINISH
    Caption set karta hai aur scheduling confirm karta hai.
    """
    payload = meta_auth.get_auth_payload(is_page=True)
    payload.update({
        "upload_phase": "finish",
        "upload_session_id": upload_session_id,
        "description": caption,
        "published": "false",
        "scheduled_publish_time": scheduled_time_unix,
    })

    response = session.post(f"{BASE_URL}/{config.PAGE_ID}/videos", data=payload)
    if not response.ok:
        raise Exception(f"Finish Phase Error: {response.text}")

    result = response.json()
    if not result.get("success"):
        raise Exception(f"Finish Phase Ambiguous Response (no success flag): {result}")

    return video_id


def upload_and_schedule_video(file_path, caption, scheduled_time_unix):
    """
    Main entry point — scheduler.py isi function ko call karta hai.
    Internally official 3-Phase Chunked Upload Protocol use karta hai
    (start -> transfer loop -> finish), seedhe /PAGE_ID/videos endpoint par.

    Returns: video_id (jo schedule hua post/video ka ID hai)
    """
    try:
        # Phase 1 & 3 ke liye normal retry-session theek hai (idempotent / light calls).
        normal_session = meta_auth.get_secure_session(retry_post=True)
        # Phase 2 (binary upload) ke liye retry OFF — duplicate-byte issue se bachne ke liye.
        upload_session = meta_auth.get_secure_session(retry_post=False)

        upload_session_id, video_id, start_offset, end_offset, file_size = _start_upload_session(
            file_path, normal_session
        )

        _transfer_chunks(
            file_path, upload_session_id, start_offset, end_offset, file_size, upload_session
        )

        final_video_id = _finish_upload(
            upload_session_id, video_id, caption, scheduled_time_unix, normal_session
        )

        return final_video_id

    except Exception as e:
        raise Exception(str(e))


def upload_and_schedule_image(file_path, caption, scheduled_time_unix):
    """
    Facebook Page Photo scheduling - simple single POST
    """
    try:
        url = f"{BASE_URL}/{config.PAGE_ID}/photos"
        payload = meta_auth.get_auth_payload(is_page=True)
        payload.update({
            "published": "false",
            "scheduled_publish_time": scheduled_time_unix,
            "caption": caption,
        })
        
        session = meta_auth.get_secure_session()
        with open(file_path, 'rb') as f:
            files = {'source': f}
            response = session.post(url, data=payload, files=files)
        
        if not response.ok:
            raise Exception(f"Image Upload Error: {response.text}")
        
        result = response.json()
        return result.get("id") or result.get("post_id")
    
    except Exception as e:
        raise Exception(str(e))
