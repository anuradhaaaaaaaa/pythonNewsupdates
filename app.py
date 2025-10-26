import os
import json
from datetime import datetime, timezone
import requests
from flask import Flask, jsonify, render_template_string
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("GNEWS_API_KEY", "2cc0f5ffb33045d88bb9858440e5e5d6")  # Keep in .env in production
CACHE_PATH = "cache/news.json"
QUERY = 'gold price OR "gold market" OR "bullion price" OR "gold rate" OR "gold market update" OR "gold investment" OR "gold demand"'  # Focus on price/market
MAX_ARTICLES = 10  # fetch more, then filter
LANG = "en"

app = Flask(__name__)

# ===== IMPACT SCORING FUNCTION =====
IMPACT_KEYWORDS = {
    "high": [
        "fed", "federal reserve", "interest rate", "dollar", "usd", "bond yield",
        "gold price", "gold rate", "gold market", "bullion price", "gold demand",
        "crisis", "war", "oil price", "inflation", "recession", "central bank"
    ],
    "medium": [
        "inflation", "cpi", "recession", "economy", "economic", "gold investment",
        "jewellery", "jewelry", "etf", "reserve", "import duty"
    ]
}

def calculate_impact_score(text: str) -> int:
    """Return impact score based on keyword matches."""
    if not text:
        return 0
    text = text.lower()
    score = 0

    for word in IMPACT_KEYWORDS["high"]:
        if word in text:
            score += 3
    for word in IMPACT_KEYWORDS["medium"]:
        if word in text:
            score += 1

    return score

# ===== CACHE HELPERS =====
def ensure_cache_dir():
    d = os.path.dirname(CACHE_PATH)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def read_cache():
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_updated": None, "articles": []}

def write_cache(obj):
    ensure_cache_dir()
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# ===== RELEVANCE FILTERING FUNCTION =====
def is_gold_price_relevant(article: dict) -> bool:
    """Filter out irrelevant articles (jewelry, politics, music, etc.)."""
    title = article.get("title", "").lower()
    desc = article.get("description", "").lower()

    # ❌ Remove irrelevant topics
    irrelevant_keywords = [
        "jewelry", "ring", "necklace", "wedding", "fashion", "music",
        "war", "conflict", "politics", "election", "government", "economy",
        "currency", "dollar", "interest rate", "bond", "inflation",
        "central bank", "federal reserve", "yield", "interest", "bond"
    ]

    for kw in irrelevant_keywords:
        if kw in title or kw in desc:
            return False

    # ✅ Keep only articles mentioning price, market, demand, investment
    relevant_keywords = [
        "price", "rate", "market", "update", "trend", "demand", "supply",
        "value", "investment", "bullion", "gold market"
    ]

    for kw in relevant_keywords:
        if kw in title or kw in desc:
            return True

    return False

# ===== FETCH & CACHE NEWS =====
def fetch_and_cache_news():
    url = "https://gnews.io/api/v4/search"
    params = {
        "q": QUERY,
        "lang": LANG,
        "max": MAX_ARTICLES * 2,  # fetch more to filter
        "apikey": API_KEY
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        app.logger.error("GNews API failed: %s", e)
        return

    articles = []
    for a in data.get("articles", []):
        title = a.get("title") or ""
        desc = a.get("description") or ""
        score = calculate_impact_score(title + " " + desc)

        # ✅ Only keep articles relevant to gold price/market
        if not is_gold_price_relevant(a):
            continue

        articles.append({
            "title": title,
            "url": a.get("url"),
            "publishedAt": a.get("publishedAt"),
            "description": desc,
            "source": a.get("source", {}).get("name"),
            "impact_score": score
        })

    # Sort by impact score (highest first)
    articles = sorted(articles, key=lambda x: x["impact_score"], reverse=True)
    articles = articles[:5]  # keep top 5 most impactful

    cache_obj = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "articles": articles
    }

    write_cache(cache_obj)
    app.logger.info(f"Cached {len(articles)} relevant gold price articles")

# ===== DAILY SCHEDULER =====
scheduler = BackgroundScheduler(timezone=timezone.utc)
scheduler.add_job(fetch_and_cache_news, 'cron', hour=2, minute=30)  # Runs daily at 2:30 AM UTC
scheduler.start()

# Initial load
with app.app_context():
    if not read_cache().get("last_updated"):
        fetch_and_cache_news()

# ===== ROUTES =====
@app.route("/news")
def news_api():
    return jsonify(read_cache())

# ===== FRONTEND (No Refresh Button) =====
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Gold News – Daily Top 5</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color:#f8f9fa; margin:0; }
    header { background:#2c3e50; color:white; padding:1.3rem; text-align:center; }
    .container { max-width:800px; margin:1.5rem auto; padding:0 1rem; }
    .card { background:white; border-radius:10px; padding:1.3rem; margin-bottom:1rem; box-shadow:0 4px 6px rgba(0,0,0,0.1); }
    .title { font-size:1.2rem; font-weight:600; color:#2c3e50; text-decoration:none; }
    .title:hover { color:#3498db; }
    .meta { font-size:0.9rem; color:#777; margin:0.3rem 0; }
    .desc { color:#555; line-height:1.5; margin-top:0.5rem; }
    .badge { padding:4px 8px; border-radius:4px; font-size:0.75rem; color:white; background:#27ae60; float:right; }
  </style>
</head>
<body>
  <header><h2>Gold News – Daily Top 5 (Ranked by Impact)</h2></header>
  <div class="container">
    <div id="status" style="margin:0.5rem 0;color:#555;">Loading...</div>
    <div id="list"></div>
  </div>

  <script>
    async function loadNews(){
      document.getElementById("status").textContent = "Loading news…";
      try {
        const r = await fetch("/news");
        const j = await r.json();
        document.getElementById("status").textContent = "Last updated: " + (j.last_updated || "unknown");
        const list = document.getElementById("list");
        list.innerHTML = "";
        (j.articles || []).forEach(a => {
          const c = document.createElement("div");
          c.className = "card";
          c.innerHTML = `
            <span class="badge">Impact: ${a.impact_score}</span>
            <a class="title" href="${a.url}" target="_blank">${a.title}</a>
            <div class="meta">${a.source || ""} — ${a.publishedAt || ""}</div>
            <div class="desc">${a.description || ""}</div>
          `;
          list.appendChild(c);
        });
      } catch(err){
        document.getElementById("status").textContent = "Error loading news.";
        console.error(err);
      }
    }

    loadNews();
    // Refresh every 5 minutes (cache is updated daily, so no need for force refresh)
    setInterval(loadNews, 5 * 60 * 1000);
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
