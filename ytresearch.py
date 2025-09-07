import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import isodate

# -----------------------------
# YOUR API KEY
# -----------------------------
API_KEY = "AIzaSyA_ZlzeFL9fEVJoG93Ii1VHZ58aTSzckpw"
youtube = build("youtube", "v3", developerKey=API_KEY)


def parse_duration(duration_str):
    """Convert ISO 8601 duration (PT#M#S) → seconds"""
    try:
        return int(isodate.parse_duration(duration_str).total_seconds())
    except:
        return 0


def youtube_filter(keywords, video_type="video", days=7, min_views=1000,
                   max_subs=50000, max_results=50, video_min_len=0, video_max_len=99999):
    results = []
    published_after = (datetime.utcnow() - timedelta(days=days)).isoformat("T") + "Z"

    # Always fetch any, then filter manually
    search_response = youtube.search().list(
        q=keywords,
        type="video",
        part="id,snippet",
        maxResults=50,
        publishedAfter=published_after,
        videoDuration="any"
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
    if not video_ids:
        return []

    video_response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=",".join(video_ids)
    ).execute()

    for video in video_response.get("items", []):
        try:
            vid_id = video["id"]
            title = video["snippet"]["title"]
            channel_id = video["snippet"]["channelId"]
            channel_title = video["snippet"]["channelTitle"]
            views = int(video["statistics"].get("viewCount", 0))
            duration_sec = parse_duration(video["contentDetails"]["duration"])

            # ✅ Shorts = ≤ 180s (3 minutes)
            if video_type.lower() == "shorts":
                if duration_sec > 180:
                    continue

            # ✅ Videos = > 180s (apply interval filter)
            if video_type.lower() == "video":
                if duration_sec <= 180:
                    continue
                if not (video_min_len * 60 <= duration_sec <= video_max_len * 60):
                    continue

            if views < min_views:
                continue

            channel_response = youtube.channels().list(
                part="statistics",
                id=channel_id
            ).execute()

            subs = int(channel_response["items"][0]["statistics"].get("subscriberCount", 0))

            if subs > max_subs:
                continue

            results.append({
                "title": title,
                "channel": channel_title,
                "views": views,
                "subscribers": subs,
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "duration_sec": duration_sec
            })

            if len(results) >= max_results:
                break

        except Exception as e:
            st.error(f"Error parsing video: {e}")
            continue

    return results


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("📺 YouTube Video Finder")

keywords = st.text_input("Enter search keywords:")
video_type = st.selectbox("Select type:", ["Video", "Shorts"])
days = st.number_input("Max video age (days):", min_value=1, max_value=365, value=7)
min_views = st.number_input("Minimum views:", min_value=0, value=1000)
max_subs = st.number_input("Maximum channel subscribers:", min_value=0, value=50000)
max_results = st.slider("Max results:", 10, 50, 20)

# Extra video length filter (only for Video)
video_min_len, video_max_len = 0, 99999
if video_type == "Video":
    length_option = st.selectbox(
        "Select video length interval (minutes):",
        ["Any", "1–10", "10–20", "20–30", "30–40", "40–50"]
    )

    if length_option != "Any":
        min_map = {"1–10": 1, "10–20": 10, "20–30": 20, "30–40": 30, "40–50": 40}
        max_map = {"1–10": 10, "10–20": 20, "20–30": 30, "30–40": 40, "40–50": 50}

        video_min_len = min_map[length_option]
        video_max_len = max_map[length_option]

if st.button("Search"):
    if keywords.strip() == "":
        st.warning("Please enter keywords.")
    else:
        with st.spinner("Searching YouTube..."):
            filtered_videos = youtube_filter(
                keywords, video_type, days, min_views, max_subs, max_results,
                video_min_len, video_max_len
            )

        if not filtered_videos:
            st.info("No videos found matching your criteria.")
        else:
            st.success(f"Found {len(filtered_videos)} videos!")
            for v in filtered_videos:
                minutes = v['duration_sec'] // 60
                seconds = v['duration_sec'] % 60
                duration_str = f"{minutes}:{seconds:02d}"
                st.markdown(
                    f"**[{v['title']}]({v['url']})**  \n"
                    f"Channel: {v['channel']}  \n"
                    f"Views: {v['views']} | Subs: {v['subscribers']} | Duration: {duration_str}"
                )
