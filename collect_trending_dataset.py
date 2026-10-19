"""
collect_trending_dataset.py

Collects ~5,000 real YouTube video records across multiple countries and categories
using the YouTube Data API v3 (videos().list endpoint) for Data Engineering projects.

Features:
- Consumes minimal API quota (uses videos().list which costs only 1 unit per 50 videos).
- Flattens nested JSON into a clean, tabular schema suitable for SQL, Spark, Pandas, and dbt.
- Parses ISO 8601 durations into duration_seconds.
- Exports to CSV and JSONL formats.
- Supports deduplication and configurable targets.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Comprehensive list of regions across North America, Europe, Asia, Latin America, Oceania, Africa
DEFAULT_REGIONS = [
    "US", "GB", "CA", "AU", "IN", "DE", "FR", "JP", "KR", "BR",
    "MX", "IT", "ES", "NL", "PL", "ID", "PH", "SG", "MY", "VN",
    "TH", "TR", "SA", "AE", "EG", "NG", "ZA", "NZ", "AR", "CO",
    "CL", "PE", "SE", "NO", "DK", "FI", "IE", "CH", "AT", "BE",
    "PT", "CZ", "RO", "HU", "GR", "IL", "TW", "HK", "PK", "BD"
]

# Popular YouTube Categories
POPULAR_CATEGORIES = ["10", "20", "24", "17", "25", "28", "23", "26", "1"]

# Mapping of standard YouTube Category IDs
CATEGORY_MAP = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Short Movies",
    "19": "Travel & Events",
    "20": "Gaming",
    "21": "Videoblogging",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
    "30": "Movies",
    "31": "Anime/Animation",
    "32": "Action/Adventure",
    "33": "Classics",
    "34": "Comedy",
    "35": "Documentary",
    "36": "Drama",
    "37": "Family",
    "38": "Foreign",
    "39": "Horror",
    "40": "Sci-Fi/Fantasy",
    "41": "Thriller",
    "42": "Shorts",
    "43": "Shows",
    "44": "Trailers",
}

ISO_DURATION_REGEX = re.compile(
    r"P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
)


def parse_iso_duration(duration_str: str) -> int:
    """Converts ISO 8601 duration (e.g., 'PT15M33S') to total seconds."""
    if not duration_str:
        return 0
    match = ISO_DURATION_REGEX.match(duration_str)
    if not match:
        return 0
    parts = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
    return (
        parts.get("days", 0) * 86400
        + parts.get("hours", 0) * 3600
        + parts.get("minutes", 0) * 60
        + parts.get("seconds", 0)
    )


def load_api_key() -> str:
    """Loads API key from .env or environment variable."""
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key or api_key.strip() == "" or api_key == "your_api_key_here":
        print("\n[ERROR] YouTube API Key is missing or not configured!", file=sys.stderr)
        print("Please ensure your API key is in the .env file (YOUTUBE_API_KEY=AIzaSy...)\n", file=sys.stderr)
        sys.exit(1)
    return api_key.strip()


def extract_record(item: dict, region_code: str, collected_at: str) -> dict:
    """Flattens a raw YouTube API item dictionary into a data engineering record."""
    video_id = item.get("id", "")
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    content = item.get("contentDetails", {})

    category_id = snippet.get("categoryId", "")
    category_name = CATEGORY_MAP.get(str(category_id), "Other")

    tags = snippet.get("tags", [])
    tags_str = "|".join(tags) if isinstance(tags, list) else ""

    raw_duration = content.get("duration", "")
    duration_secs = parse_iso_duration(raw_duration)

    thumbnails = snippet.get("thumbnails", {})
    thumb_url = (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url", "")
    )

    # Sanitize multiline description for CSV friendliness (keep first 300 chars)
    desc = snippet.get("description", "").replace("\r", " ").replace("\n", " ").strip()
    if len(desc) > 300:
        desc = desc[:297] + "..."

    return {
        "video_id": video_id,
        "title": snippet.get("title", ""),
        "channel_id": snippet.get("channelId", ""),
        "channel_title": snippet.get("channelTitle", ""),
        "published_at": snippet.get("publishedAt", ""),
        "category_id": category_id,
        "category_name": category_name,
        "trending_region": region_code,
        "collected_at": collected_at,
        "duration_iso": raw_duration,
        "duration_seconds": duration_secs,
        "view_count": int(stats.get("viewCount", 0)),
        "like_count": int(stats.get("likeCount", 0)),
        "comment_count": int(stats.get("commentCount", 0)),
        "definition": content.get("definition", ""),
        "caption": content.get("caption", "false") == "true",
        "licensed_content": content.get("licensedContent", False),
        "tags": tags_str,
        "thumbnail_url": thumb_url,
        "description": desc,
    }


def fetch_dataset(youtube, target_count: int = 5000, dedup: bool = True, delay: float = 0.05) -> list:
    """
    Collects records across regions and categories until target_count is reached.
    """
    records = []
    seen_video_ids = set()
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"\nTarget: {target_count} records | Deduplication: {dedup}")
    print(f"Iterating across {len(DEFAULT_REGIONS)} regions...\n")

    api_call_count = 0

    # Pass 1: Global trending across regions
    for region in DEFAULT_REGIONS:
        if len(records) >= target_count:
            break

        next_page_token = None
        pages_for_region = 0
        # Usually each region has up to 4 pages (200 items)
        max_pages_per_region = 4

        while pages_for_region < max_pages_per_region:
            if len(records) >= target_count:
                break

            try:
                params = {
                    "part": "snippet,contentDetails,statistics",
                    "chart": "mostPopular",
                    "regionCode": region,
                    "maxResults": 50,
                }
                if next_page_token:
                    params["pageToken"] = next_page_token

                req = youtube.videos().list(**params)
                res = req.execute()
                api_call_count += 1

                items = res.get("items", [])
                if not items:
                    break

                new_in_page = 0
                for item in items:
                    vid = item.get("id")
                    if dedup:
                        if vid in seen_video_ids:
                            continue
                        seen_video_ids.add(vid)

                    record = extract_record(item, region_code=region, collected_at=collected_at)
                    records.append(record)
                    new_in_page += 1

                    if len(records) >= target_count:
                        break

                print(f"[{region}] Page {pages_for_region + 1}: +{new_in_page} records | Total: {len(records)}/{target_count} (API units: {api_call_count})")

                next_page_token = res.get("nextPageToken")
                pages_for_region += 1

                if not next_page_token:
                    break

                time.sleep(delay)

            except HttpError as err:
                print(f"\n[Warning] API error for region {region}: {err._get_reason()}")
                if err.resp.status == 403:
                    print("[Error] Quota exceeded or permission denied. Stopping collection.")
                    return records
                break
            except Exception as e:
                print(f"[Warning] Error on region {region}: {e}")
                break

    # Pass 2: If we still need more records, query specific categories in top regions
    if len(records) < target_count:
        print(f"\nPass 1 complete ({len(records)} records). Collecting by specific categories for more variety...")
        top_regions = ["US", "GB", "IN", "CA", "AU", "DE", "BR"]

        for region in top_regions:
            if len(records) >= target_count:
                break

            for cat_id in POPULAR_CATEGORIES:
                if len(records) >= target_count:
                    break

                next_page_token = None
                cat_pages = 0
                cat_name = CATEGORY_MAP.get(cat_id, cat_id)

                while cat_pages < 2:  # 2 pages per category
                    if len(records) >= target_count:
                        break

                    try:
                        params = {
                            "part": "snippet,contentDetails,statistics",
                            "chart": "mostPopular",
                            "regionCode": region,
                            "videoCategoryId": cat_id,
                            "maxResults": 50,
                        }
                        if next_page_token:
                            params["pageToken"] = next_page_token

                        req = youtube.videos().list(**params)
                        res = req.execute()
                        api_call_count += 1

                        items = res.get("items", [])
                        if not items:
                            break

                        new_in_cat = 0
                        for item in items:
                            vid = item.get("id")
                            if dedup:
                                if vid in seen_video_ids:
                                    continue
                                seen_video_ids.add(vid)

                            record = extract_record(item, region_code=region, collected_at=collected_at)
                            records.append(record)
                            new_in_cat += 1

                            if len(records) >= target_count:
                                break

                        print(f"[{region} - {cat_name}] Page {cat_pages + 1}: +{new_in_cat} records | Total: {len(records)}/{target_count} (API units: {api_call_count})")

                        next_page_token = res.get("nextPageToken")
                        cat_pages += 1
                        if not next_page_token:
                            break

                        time.sleep(delay)

                    except HttpError as err:
                        if err.resp.status == 403:
                            print("[Error] Quota exceeded. Stopping.")
                            return records
                        break
                    except Exception:
                        break

    print(f"\nDone! Total records collected: {len(records)} using {api_call_count} API quota units.")
    return records


def save_to_csv(records: list, output_path: Path):
    """Saves records to CSV file."""
    if not records:
        print("[Warning] No records to save.")
        return

    fieldnames = list(records[0].keys())
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(records)

    print(f"[Saved] CSV file: {output_path.resolve()} ({output_path.stat().st_size / (1024 * 1024):.2f} MB)")


def save_to_jsonl(records: list, output_path: Path):
    """Saves records to JSON Lines file (one JSON object per line)."""
    if not records:
        return

    with open(output_path, mode="w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[Saved] JSONL file: {output_path.resolve()} ({output_path.stat().st_size / (1024 * 1024):.2f} MB)")


def main():
    parser = argparse.ArgumentParser(
        description="Collect ~5,000 YouTube trending video records across countries and categories for Data Engineering."
    )
    parser.add_argument(
        "-t", "--target",
        type=int,
        default=5000,
        help="Target number of records to collect (default: 5000)"
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="youtube_trending_5000.csv",
        help="Output CSV filename (default: youtube_trending_5000.csv)"
    )
    parser.add_argument(
        "--output-jsonl",
        type=str,
        default="youtube_trending_5000.jsonl",
        help="Output JSONL filename (default: youtube_trending_5000.jsonl)"
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="If set, allows the same video across different trending regions (snapshots)."
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Delay in seconds between API calls (default: 0.05)"
    )

    args = parser.parse_args()

    api_key = load_api_key()
    youtube = build("youtube", "v3", developerKey=api_key)

    records = fetch_dataset(
        youtube=youtube,
        target_count=args.target,
        dedup=not args.allow_duplicates,
        delay=args.delay
    )

    script_dir = Path(__file__).resolve().parent
    csv_file = script_dir / args.output_csv
    jsonl_file = script_dir / args.output_jsonl

    save_to_csv(records, csv_file)
    save_to_jsonl(records, jsonl_file)

    print("\nDataset ready for Data Engineering pipelines (ETL, BigQuery, Spark, Postgres, dbt)!")


if __name__ == "__main__":
    main()
