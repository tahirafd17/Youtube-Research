from googleapiclient.discovery import build
from datetime import datetime, timedelta

# -----------------------------
# SET YOUR API KEY
# -----------------------------
API_KEY = "AIzaSyA_ZlzeFL9fEVJoG93Ii1VHZ58aTSzckpw"
youtube = build("youtube", "v3", developerKey=API_KEY)


def youtube_filter(keywords, video_type="video", days=7, min_views=1000, max_subs=50000, max_results=50):
    results = []
    
    published_after = (datetime.utcnow() - timedelta(days=days)).isoformat("T") + "Z"

    print(f"[DEBUG] Searching for '{keywords}' | Type: {video_type} | Days: {days} | Min Views: {min_views} | Max Subs: {max_subs}")

    search_response = youtube.search().list(
        q=keywords,
        type="video",
        part="id,snippet",
        maxResults=50,
        publishedAfter=published_after,
        videoDuration="short" if video_type.lower() == "shorts" else "any"
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

    if not video_ids:
        print("[DEBUG] No videos found for given criteria.")
        return []

    video_response = youtube.videos().list(
        part="snippet,statistics",
        id=",".join(video_ids)
    ).execute()

    for video in video_response.get("items", []):
        try:
            vid_id = video["id"]
            title = video["snippet"]["title"]
            channel_id = video["snippet"]["channelId"]
            channel_title = video["snippet"]["channelTitle"]
            views = int(video["statistics"].get("viewCount", 0))

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
                "video_id": vid_id,
                "title": title,
                "channel": channel_title,
                "views": views,
                "subscribers": subs,
                "url": f"https://www.youtube.com/watch?v={vid_id}"
            })

            if len(results) >= max_results:
                break

        except Exception as e:
            print(f"[ERROR] Error parsing video: {e}")
            continue

    return results


if __name__ == "__main__":
    keywords = input("Enter search keywords: ")
    video_type = input("Enter type (Shorts/Video): ")
    days = int(input("Enter max video age (days): "))
    min_views = int(input("Enter minimum views: "))
    max_subs = int(input("Enter maximum channel subscribers: "))

    filtered_videos = youtube_filter(keywords, video_type, days, min_views, max_subs)

    print("\n================= FILTERED VIDEOS =================")
    for idx, v in enumerate(filtered_videos, 1):
        print(f"{idx}. {v['title']} | {v['channel']} | {v['views']} views | {v['subscribers']} subs")
        print(f"   {v['url']}")
