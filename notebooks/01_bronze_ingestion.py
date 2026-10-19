
# YouTube Trends & Engagement Analytics
# Notebook 01: Bronze ingestion

# Step 1: Import the tools we need
import json
import os
from datetime import datetime, timezone

import requests

# Step 2: Read the YouTube API key from an environment variable
# We will configure this securely in Fabric later.
API_KEY = os.environ.get("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError(
        "YouTube API key is missing. "
        "Configure YOUTUBE_API_KEY before running this code."
    )

# Step 3: Define the YouTube API endpoint
URL = "https://www.googleapis.com/youtube/v3/videos"

# Step 4: Choose what data we want
params = {
    "part": "snippet,contentDetails,statistics",
    "chart": "mostPopular",
    "regionCode": "AU",
    "maxResults": 50,
    "key": API_KEY
}

# Step 5: Request the data from YouTube
response = requests.get(URL, params=params, timeout=30)

# Step 6: Stop if YouTube returns an error
response.raise_for_status()

# Step 7: Convert the response into Python data
data = response.json()

# Step 8: Record when we collected the data
collected_at = datetime.now(timezone.utc).isoformat()

# Step 9: Add collection time to our data
bronze_record = {
    "collected_at": collected_at,
    "region": "AU",
    "response": data
}

# Step 10: Display a small summary
videos = data.get("items", [])

print("Region: Australia")
print("Videos retrieved:", len(videos))
print("Collected at:", collected_at)

for video in videos[:5]:
    snippet = video.get("snippet", {})
    statistics = video.get("statistics", {})

    print("\nTitle:", snippet.get("title", "Unknown"))
    print("Views:", statistics.get("viewCount", "Not available"))
