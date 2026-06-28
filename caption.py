from datetime import datetime

# ==========================================================
# QuizWala Caption Engine v2.0
# ==========================================================

def format_date(dt):
    """
    Convert datetime/date -> '28 June 2026'
    """
    return dt.strftime("%d %B %Y")


def get_video_caption(date_text: str, part_num: str) -> str:
    """
    Generates caption for video reels.

    Example:
        get_video_caption("28 June 2026", "Part-1")
    """

    return f"""{date_text} Current Affairs Quiz | {part_num} 🧠

Score 3/3?

Comment "GK MASTER"

Follow @the_quizwala

YT : @The_QuizWala
FB : @TheQuizWala

#currentaffairs
#gkquiz
#ssc
#upsc
#railway
#quizwala"""


def get_image_caption() -> str:
    """
    Image post will be uploaded WITHOUT caption.
    """
    return ""


# ==========================================================
# Test
# ==========================================================
if __name__ == "__main__":

    today = format_date(datetime.now())

    print("=" * 50)
    print(get_video_caption(today, "Part-3"))
    print("=" * 50)
    print(repr(get_image_caption()))