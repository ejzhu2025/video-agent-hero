# adreel Marketing Module

Automated ad video generation and social media outreach pipeline.

**What it does:** Discover brands → scrape their website → generate a 9:16 ad video → produce platform-ready copy and covers for TikTok, Instagram, and 小红书 → track post performance.

---

## Quickstart

```bash
cd /Users/bytedance/Desktop/ads_video_hero
pip install -e .

# Generate a content package for one brand
python -m marketing.cli new --url https://allbirds.com --size medium

# Output lands in:
# marketing/output/2026-03-21/allbirds/
#   video.mp4
#   cover_tiktok.jpg
#   cover_instagram.jpg
#   tiktok.txt
#   instagram.txt
```

---

## Required Environment Variables

Add these to `ads_video_hero/.env`:

```env
# Core (required)
ANTHROPIC_API_KEY=sk-ant-...        # video generation + copy writing

# Brand scraping (recommended)
GOOGLE_API_KEY=...                  # Gemini for smart brand extraction

# Brand discovery (optional)
PRODUCT_HUNT_TOKEN=...              # find brands from Product Hunt

# Analytics sync (optional — set up after Instagram API approval)
INSTAGRAM_ACCESS_TOKEN=...          # pull post metrics automatically
```

---

## Commands

### `new` — Generate ad for one brand
```bash
python -m marketing.cli new \
  --url https://gymshark.com \
  --size medium \
  --quality turbo \
  --platforms tiktok,instagram
```

Options:
- `--size` `large` / `medium` / `small` — used in analytics grouping
- `--quality` `turbo` (fast, cheaper) / `hd` (slower, better)
- `--platforms` comma-separated: `tiktok`, `instagram`, `xiaohongshu`

---

### `batch` — Process a CSV file
```bash
python -m marketing.cli batch --file brands.csv --limit 10
```

CSV format:
```csv
url,name,category,size
https://allbirds.com,Allbirds,fashion,medium
https://notion.so,Notion,saas,large
https://glossier.com,Glossier,beauty,large
```

---

### `find` — Discover brands from Product Hunt
```bash
# Find 10 brands and print them
python -m marketing.cli find --count 10 --category fashion

# Find AND immediately generate ads
python -m marketing.cli find --count 5 --run
```

---

### `log` — Record that you posted
After manually posting a video, log it:
```bash
python -m marketing.cli log \
  --campaign proj_abc123 \
  --platform instagram \
  --post-id 17896132429627826
```

---

### `sync` — Pull Instagram analytics
```bash
python -m marketing.cli sync \
  --post post_xyz456 \
  --media-id 17896132429627826
```

Requires `INSTAGRAM_ACCESS_TOKEN` in `.env`. See [Instagram API Setup](#instagram-api-setup) below.

---

### `report` — Conversion analysis
```bash
python -m marketing.cli report
```

Output:
```
Size     Platform    Campaigns  Posts  Avg Views  Avg Likes  Total DMs  DM Rate %
large    instagram   5          5      12400      430        8          1.6
medium   instagram   12         12     4200       180        11         0.92
small    tiktok      8          8      900        60         2          0.25
```

Use this to find which brand size converts best on which platform.

---

## Output Structure

Each campaign produces:

```
marketing/output/
└── 2026-03-21/
    └── allbirds/
        ├── video.mp4              9:16 H.264 ad video (1080×1920)
        ├── cover_tiktok.jpg       9:16 cover frame
        ├── cover_instagram.jpg    9:16 cover frame
        ├── cover_xiaohongshu.jpg  3:4 cover frame (1080×1440)
        ├── tiktok.txt             Title + body + CTA + hashtags (English)
        ├── instagram.txt          Title + body + CTA + hashtags (English)
        └── xiaohongshu.txt        Title + body + CTA + hashtags (Chinese)
```

---

## Full Pipeline Flow

```
marketing new --url X
      │
      ▼
1. brand_finder.py       BrandLead(url, size, category)
      │
      ▼
2. scrape_product.py     Scrape website → brand_info (name, colors, brief, logo)
      │
      ▼
3. campaign_runner.py    Create BrandKit + project in DB
      │
      ▼
4. ads_video_hero        LangGraph pipeline → 9:16 MP4
   pipeline
      │
      ▼
5. content_packager.py   Extract covers + Claude-generated copy (3 platforms)
      │
      ▼
6. tracker.py            Record campaign in marketing.db
      │
      ▼
   output/{date}/{brand}/
   (post manually to TikTok / Instagram / 小红书)
      │
      ▼
7. marketing log         Record post ID
8. marketing sync        Pull Instagram metrics via Graph API
9. marketing report      See which brand size converts best
```

---

## Instagram API Setup

To auto-pull analytics after posting:

1. Convert your Instagram account to **Business** (Settings → Account → Switch to Professional)
2. Connect it to a **Facebook Page**
3. Go to [developers.facebook.com](https://developers.facebook.com) → Create App → Consumer
4. Add product: **Instagram Graph API**
5. Generate a long-lived User Access Token with scopes: `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`
6. Add token to `.env`:
   ```env
   INSTAGRAM_ACCESS_TOKEN=EAABsbCS...
   ```

---

## TikTok API Setup

1. Go to [developers.tiktok.com](https://developers.tiktok.com) → Create App
2. Request scopes: `video.publish`, `video.list`
3. Submit for review (requires a working product demo — use adreel.studio)
4. After approval, implement OAuth flow to get user tokens

TikTok analytics are available via TikTok for Business API (separate approval).

---

## Data

All campaign and post records are stored in:
```
marketing/data/marketing.db   (SQLite)
```

Tables: `campaigns`, `posts`
