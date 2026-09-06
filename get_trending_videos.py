"""
get_trending_videos.py

A Python script to authenticate with Google's YouTube Data API v3 
and fetch trending videos for a specified region without hardcoding credentials.
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def load_api_key() -> str:
    """
    Loads the YouTube API key from environment variables or a local .env file.
    """
    # Look for .env file in the same directory as this script
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir / ".env"

    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # Fallback to default load_dotenv (looks in current working directory)
        load_dotenv()

    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key or api_key.strip() == "" or api_key == "your_api_key_here":
        print("\n[ERROR] YouTube API Key is missing or not configured!", file=sys.stderr)
        print("\nPlease follow these steps to configure your API key:", file=sys.stderr)
        print(f"  1. Copy '.env.example' to '.env' in: {script_dir}", file=sys.stderr)
        print("  2. Open '.env' and paste your Google API key:", file=sys.stderr)
        print("     YOUTUBE_API_KEY=AIzaSyYourActualKeyHere", file=sys.stderr)
        print("  3. Re-run the script.\n", file=sys.stderr)
        sys.exit(1)

    return api_key.strip()


def get_trending_videos(api_key: str, region_code: str = "US", max_results: int = 10, category_id: str = None) -> list:
    """
    Queries the YouTube Data API v3 videos endpoint for mostPopular (trending) videos.

    Args:
        api_key: Google API Key with YouTube Data API v3 enabled.
        region_code: ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'IN', 'AU').
        max_results: Number of results to retrieve (between 1 and 50).
        category_id: Optional YouTube video category ID to filter by.

    Returns:
        List of video item dictionaries returned by the API.
    """
    try:
        youtube = build("youtube", "v3", developerKey=api_key)

        request_params = {
            "part": "snippet,contentDetails,statistics",
            "chart": "mostPopular",
            "regionCode": region_code.upper(),
            "maxResults": min(max(1, max_results), 50),
        }

        if category_id:
            request_params["videoCategoryId"] = category_id

        request = youtube.videos().list(**request_params)
        response = request.execute()

        return response.get("items", [])

    except HttpError as err:
        print(f"\n[API Error] HTTP {err.resp.status}: {err._get_reason()}", file=sys.stderr)
        if err.resp.status == 400:
            print("Hint: Check if the region code is a valid ISO 3166-1 alpha-2 code (e.g., US, IN, GB).", file=sys.stderr)
        elif err.resp.status == 403:
            print("Hint: Verify that 'YouTube Data API v3' is enabled in your Google Cloud Console", file=sys.stderr)
            print("      and that your API key is correct and not restricted or quota-limited.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[Unexpected Error]: {e}", file=sys.stderr)
        sys.exit(1)


def display_videos(videos: list, region_code: str):
    """
    Prints the trending videos in a clean, human-readable format.
    """
    if not videos:
        print(f"\nNo trending videos found for region '{region_code}'.")
        return

    print("=" * 80)
    print(f"  TRENDING YOUTUBE VIDEOS ({region_code.upper()}) - Top {len(videos)}")
    print("=" * 80)

    for index, item in enumerate(videos, start=1):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        video_id = item.get("id")

        title = snippet.get("title", "Unknown Title")
        channel = snippet.get("channelTitle", "Unknown Channel")
        published_at = snippet.get("publishedAt", "")[:10]  # Extract YYYY-MM-DD
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        print(f"\n#{index} {title}")
        print(f"    Channel:   {channel}")
        print(f"    Published: {published_at}")
        print(f"    Views:     {views:,}")
        print(f"    Likes:     {likes:,}")
        print(f"    URL:       {video_url}")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch trending YouTube videos for a specific region using YouTube Data API v3."
    )
    parser.add_argument(
        "-r", "--region",
        type=str,
        default="US",
        help="ISO 3166-1 alpha-2 country code (default: US, e.g. US, IN, GB, AU, CA, JP)"
    )
    parser.add_argument(
        "-m", "--max-results",
        type=int,
        default=10,
        help="Number of trending videos to retrieve (1-50, default: 10)"
    )
    parser.add_argument(
        "-c", "--category-id",
        type=str,
        default=None,
        help="Optional YouTube category ID to filter (e.g., 10 for Music, 20 for Gaming)"
    )

    args = parser.parse_args()

    api_key = load_api_key()
    videos = get_trending_videos(
        api_key=api_key,
        region_code=args.region,
        max_results=args.max_results,
        category_id=args.category_id
    )
    display_videos(videos, region_code=args.region)


if __name__ == "__main__":
    main()
