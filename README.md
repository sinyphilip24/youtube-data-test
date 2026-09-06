# YouTube Data API v3 - Trending Videos

A Python tool to query Google's YouTube Data API v3 `videos` endpoint for trending videos in any region without hardcoding API keys.

---

## 🚀 Quick Start (via Anaconda Prompt)

### 1. Open Anaconda Prompt
Open your **Anaconda Prompt** from the Windows Start menu.

### 2. Navigate to this project folder
```cmd
cd c:\Users\sinyp\projects\youtube-data-test
```

### 3. Create and activate a Conda environment
```cmd
conda create -n youtube-api python=3.11 -y
conda activate youtube-api
```

### 4. Install dependencies
```cmd
pip install -r requirements.txt
```

---

## 🔑 Configure Your API Key

1. Copy `.env.example` to a new file named `.env`:
   ```cmd
   copy .env.example .env
   ```
2. Open `.env` in any text editor and replace `your_api_key_here` with your actual Google API key:
   ```env
   YOUTUBE_API_KEY=AIzaSyD...
   ```
*(Note: `.env` is listed in `.gitignore` so your credentials are never exposed or committed to git.)*

---

## ▶️ Running the Script

### Default (Top 10 trending in US):
```cmd
python get_trending_videos.py
```

### Specify a different region (e.g. Australia `AU`, India `IN`, Great Britain `GB`):
```cmd
python get_trending_videos.py --region AU
```

### Fetch top 25 trending videos:
```cmd
python get_trending_videos.py --region US --max-results 25
```

### Filter by Category (e.g. Music = 10, Gaming = 20):
```cmd
python get_trending_videos.py --region US --category-id 10
```

### View Help / Options:
```cmd
python get_trending_videos.py --help
```
