import os
import json
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === Configuration ===
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "market_reports_db")
PORT = int(os.getenv("PORT", 5050))

# GNews API
API_KEY = os.getenv("GNEWS_API_KEY", "2cc0f5ffb33045d88bb9858440e5e5d6")
CACHE_PATH = "cache/news.json"
QUERY = 'gold price OR "gold market" OR "bullion price" OR "gold rate" OR "gold market update" OR "gold investment" OR "gold demand"'
MAX_ARTICLES = 10
LANG = "en"

# === MongoDB Setup ===
# Handle case where MONGO_URI is missing (for local testing without DB)
if not MONGO_URI:
    print("WARNING: MONGO_URI not set. Database features will fail.")
    client = None
    reports_col = None
else:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    reports_col = db.reports

# === Impact Scoring & Filtering ===
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

def is_gold_price_relevant(article: dict) -> bool:
    """Filter out irrelevant articles (jewelry, politics, music, etc.)."""
    title = article.get("title", "").lower()
    desc = article.get("description", "").lower()

    # ❌ Remove irrelevant topics
    # FIXED: Removed economic terms (dollar, inflation, interest) from here
    # because they are actually HIGH IMPACT drivers for gold.
    irrelevant_keywords = [
        "necklace", "wedding", "fashion", "music", "concert",
        "entertainment", "gossip", "celebrity", "sport"
    ]

    for kw in irrelevant_keywords:
        if kw in title or kw in desc:
            return False

    # ✅ Keep only articles mentioning price, market, demand, investment
    relevant_keywords = [
        "price", "rate", "market", "update", "trend", "demand", "supply",
        "value", "investment", "bullion", "gold market", "dollar", "inflation", "fed"
    ]

    for kw in relevant_keywords:
        if kw in title or kw in desc:
            return True
    return False

# === Cache Helpers ===
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

# === Fetch & Cache News ===
def fetch_and_cache_news():
    print("Fetching fresh news from GNews API...")
    url = "https://gnews.io/api/v4/search"
    params = {
        "q": QUERY,
        "lang": LANG,
        "max": MAX_ARTICLES * 2,
        "apikey": API_KEY
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"GNews API failed: {e}")
        return {"error": str(e)}

    articles = []
    for a in data.get("articles", []):
        title = a.get("title") or ""
        desc = a.get("description") or ""
        score = calculate_impact_score(title + " " + desc)

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

    # Sort by impact score (highest first), limit to top 5
    articles = sorted(articles, key=lambda x: x["impact_score"], reverse=True)[:5]

    cache_obj = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "articles": articles
    }

    write_cache(cache_obj)
    print(f"Success: Cached {len(articles)} relevant gold price articles")
    return cache_obj

# === Scheduler Setup ===
scheduler = BackgroundScheduler(timezone=timezone.utc)
scheduler.add_job(fetch_and_cache_news, 'cron', hour=2, minute=30)  # Daily at 2:30 UTC
scheduler.start()

# === Initialize Flask App ===
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# === Helpers ===
def serialize_report(doc):
    doc["_id"] = str(doc["_id"])
    return doc

# === Routes: Reports CRUD ===
@app.route("/api/reports", methods=["GET"])
def get_reports():
    if not reports_col: return jsonify({"error": "DB not connected"}), 500
    title_q = request.args.get("title", None)
    if title_q:
        cursor = reports_col.find({"title": {"$regex": f"^{title_q}$", "$options": "i"}})
    else:
        cursor = reports_col.find()
    docs = [serialize_report(d) for d in cursor]
    return jsonify(docs), 200

@app.route("/api/reports/<id>", methods=["GET"])
def get_report_by_id(id):
    if not reports_col: return jsonify({"error": "DB not connected"}), 500
    try:
        doc = reports_col.find_one({"_id": ObjectId(id)})
    except Exception:
        return jsonify({"error": "invalid id"}), 400
    if not doc:
        return jsonify({"error": "not found"}), 404
    return jsonify(serialize_report(doc)), 200

@app.route("/api/reports", methods=["POST"])
def create_report():
    if not reports_col: return jsonify({"error": "DB not connected"}), 500
    data = request.json
    if not data or "title" not in data:
        return jsonify({"error": "missing title"}), 400
    data.setdefault("things", [])
    data.setdefault("links", [])
    data.setdefault("opinion", "")
    data.setdefault("result", "")
    res = reports_col.insert_one(data)
    doc = reports_col.find_one({"_id": res.inserted_id})
    return jsonify(serialize_report(doc)), 201

@app.route("/api/reports/<id>", methods=["PUT"])
def update_report(id):
    if not reports_col: return jsonify({"error": "DB not connected"}), 500
    data = request.json
    try:
        oid = ObjectId(id)
    except Exception:
        return jsonify({"error": "invalid id"}), 400
    update = {"$set": {
        "title": data.get("title"),
        "things": data.get("things", []),
        "links": data.get("links", []),
        "opinion": data.get("opinion", ""),
        "result": data.get("result", "")
    }}
    result = reports_col.update_one({"_id": oid}, update)
    if result.matched_count == 0:
        return jsonify({"error": "not found"}), 404
    doc = reports_col.find_one({"_id": oid})
    return jsonify(serialize_report(doc)), 200

@app.route("/api/reports/<id>", methods=["DELETE"])
def delete_report(id):
    if not reports_col: return jsonify({"error": "DB not connected"}), 500
    try:
        oid = ObjectId(id)
    except Exception:
        return jsonify({"error": "invalid id"}), 400
    result = reports_col.delete_one({"_id": oid})
    if result.deleted_count == 0:
        return jsonify({"error": "not found"}), 404
    return jsonify({"deleted": id}), 200

# === NEW ROUTE: Manual Force Refresh ===
@app.route("/api/news/refresh", methods=["POST"])
def force_refresh_news():
    """Manually triggers the news fetcher."""
    result = fetch_and_cache_news()
    if result and "error" in result:
        return jsonify(result), 500
    return jsonify({"status": "success", "message": "Cache updated successfully"}), 200

# === News API Route ===
@app.route("/news")
def news_api():
    return jsonify(read_cache())

# === Frontend ===
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Gold News – Daily Top 5</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color:#f8f9fa; margin:0; }
    header { background:#2c3e50; color:white; padding:1.3rem; text-align:center; display: flex; justify-content: space-between; align-items: center; padding: 1rem 2rem; }
    header h2 { margin: 0; }
    .container { max-width:800px; margin:1.5rem auto; padding:0 1rem; }
    .card { background:white; border-radius:10px; padding:1.3rem; margin-bottom:1rem; box-shadow:0 4px 6px rgba(0,0,0,0.1); }
    .title { font-size:1.2rem; font-weight:600; color:#2c3e50; text-decoration:none; }
    .title:hover { color:#3498db; }
    .meta { font-size:0.9rem; color:#777; margin:0.3rem 0; }
    .desc { color:#555; line-height:1.5; margin-top:0.5rem; }
    .badge { padding:4px 8px; border-radius:4px; font-size:0.75rem; color:white; background:#27ae60; float:right; }
    
    /* Button Styles */
    .refresh-btn {
        background-color: #e74c3c;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: background 0.3s;
    }
    .refresh-btn:hover { background-color: #c0392b; }
    .refresh-btn:disabled { background-color: #95a5a6; cursor: not-allowed; }
  </style>
</head>
<body>
  <header>
    <h2>Gold News – Daily Top 5</h2>
    <button id="refreshBtn" class="refresh-btn" onclick="forceRefresh()">Force Refresh</button>
  </header>
  
  <div class="container">
    <div id="status" style="margin:0.5rem 0;color:#555;">Loading...</div>
    <div id="list"></div>
  </div>

  <script>
    async function loadNews(){
      document.getElementById("status").textContent = "Loading news from cache...";
      try {
        const r = await fetch("/news");
        const j = await r.json();
        
        if (!j.last_updated) {
            document.getElementById("status").textContent = "No data available. Click Force Refresh.";
            return;
        }

        const date = new Date(j.last_updated).toLocaleString();
        document.getElementById("status").textContent = "Last updated: " + date;
        
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

    // === NEW: Force Refresh Logic ===
    async function forceRefresh() {
        const btn = document.getElementById("refreshBtn");
        const originalText = btn.textContent;
        
        if(!confirm("This will call the external GNews API. Continue?")) return;

        btn.disabled = true;
        btn.textContent = "Updating...";
        
        try {
            const res = await fetch("/api/news/refresh", { method: "POST" });
            const data = await res.json();
            
            if(res.ok) {
                alert("Cache updated!");
                loadNews(); // Reload the UI
            } else {
                alert("Error: " + (data.error || "Unknown error"));
            }
        } catch (e) {
            alert("Network error: " + e);
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }

    loadNews();
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

# === Start the App ===
if __name__ == "__main__":
    print("Starting Flask app...")
    print(f"Port: {PORT}")
    
    # Check if cache exists, if not, fetch once on startup
    if not os.path.exists(CACHE_PATH):
        print("No cache found. Fetching initial news...")
        fetch_and_cache_news()
        
    app.run(host="0.0.0.0", port=PORT, debug=False)
