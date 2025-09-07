import sys
import subprocess
import importlib
from datetime import datetime, timedelta

# -----------------------------
# AUTO-INSTALL CHECK
# -----------------------------
required_libs = ["googleapiclient.discovery"]
for lib in required_libs:
    try:
        importlib.import_module(lib.split('.')[0])
    except ImportError:
        print(f"[DEBUG] Missing dependency: {lib}. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-api-python-client"])
        break

from googleapiclient.discovery import build

# -----------------------------
# SET YOUR API KEY
# -----------------------------
API_KEY = "AIzaSyA_ZlzeFL9fEVJoG93Ii1VHZ58aTSzckpw"
youtube = build("youtube", "v3", developerKey=API_KEY)


def youtube_filter(keywords, video_type="video", days=7, min_views=1000, max_subs=50000, max_results=50):
    results = []
    
    # Published after (ISO 8601 format)
    published_after = (datetime.utcnow() - timedelta(days=days)).isoformat("T") + "Z"

    print(f"[DEBUG] Searching for '{keywords}' | Type: {video_type} | Days: {days} | Min Views: {min_views} | Max Subs: {max_subs}")

    try:
        # Search request
        search_response = youtube.search().list(
            q=keywords,
            type="video",
            part="id,snippet",
            maxResults=50,
            publishedAfter=published_after,
            videoDuration="short" if video_type.lower() == "shorts" else "any"
        ).execute()
    except Exception as e:
        print(f"[ERROR] Search request failed: {e}")
        return []

    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

    if not video_ids:
        print("[DEBUG] No videos found for given criteria.")
        return []

    try:
        # Get video details
        video_response = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids)
        ).execute()
    except Exception as e:
        print(f"[ERROR] Failed to fetch video details: {e}")
        return []

    for video in video_response.get("items", []):
        try:
            vid_id = video["id"]
            title = video["snippet"]["title"]
            channel_id = video["snippet"]["channelId"]
            channel_title = video["snippet"]["channelTitle"]
            views = int(video["statistics"].get("viewCount", 0))

            # Filter by views
            if views < min_views:
                print(f"[DEBUG] Skipped '{title}' (views {views} < {min_views})")
                continue

            # Get channel subs
            try:
                channel_response = youtube.channels().list(
                    part="statistics",
                    id=channel_id
                ).execute()

                subs = int(channel_response["items"][0]["statistics"].get("subscriberCount", 0))
            except Exception as e:
                print(f"[ERROR] Failed to fetch subscribers for {channel_title}: {e}")
                continue

            if subs > max_subs:
                print(f"[DEBUG] Skipped '{title}' (subs {subs} > {max_subs})")
                continue

            # Passed filters → add to results
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
    # Example usage
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

