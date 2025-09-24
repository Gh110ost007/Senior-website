import csv
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, redirect, render_template, request, url_for, abort, make_response, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import json
from markdown import markdown
import hashlib

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GUIDES_DIR = BASE_DIR / "guides"
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)
LEADS_CSV = INSTANCE_DIR / "leads.csv"
SEMINARS_CSV = INSTANCE_DIR / "seminars.csv"
DB_PATH = INSTANCE_DIR / "analytics.db"

# Load configuration
config_name = os.getenv('FLASK_ENV', 'development')
from config import config

app = Flask(__name__)
app.config.from_object(config[config_name])

# Get config values after app is configured
ADMIN_TOKEN = app.config['ADMIN_TOKEN']
SITE_URL = app.config['SITE_URL']

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access the admin area.'

# User model for authentication
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Simple user storage (in production, use a proper database)
ADMIN_USERNAME = app.config['ADMIN_USERNAME']
ADMIN_PASSWORD_HASH = hashlib.sha256(app.config['ADMIN_PASSWORD'].encode()).hexdigest()

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return User("admin", ADMIN_USERNAME, ADMIN_PASSWORD_HASH)
    return None

# Initialize database
def init_db():
    """Initialize SQLite database for analytics and progress tracking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Events table for analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            user_id TEXT,
            metadata TEXT,
            ip_address TEXT,
            user_agent TEXT
        )
    ''')
    
    # Progress tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            lesson_id TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            time_spent INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lesson_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def log_event(event_type: str, session_id: str = None, user_id: str = None, metadata: dict = None):
    """Log an event to the analytics database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO events (event_type, session_id, user_id, metadata, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        event_type,
        session_id,
        user_id,
        json.dumps(metadata) if metadata else None,
        request.remote_addr,
        request.headers.get('User-Agent', '')
    ))
    
    conn.commit()
    conn.close()


def load_topics(lang: str = "en") -> List[Dict[str, Any]]:
    if lang == "hi":
        path = DATA_DIR / "topics_hi.json"
    else:
        path = DATA_DIR / "topics.json"
    return load_json(path) if path.exists() else []


def load_guides() -> List[Dict[str, Any]]:
    path = DATA_DIR / "guides.json"
    if not path.exists():
        return []
    guides = load_json(path)
    guides.sort(key=lambda g: g.get("date", ""), reverse=True)
    return guides


def load_pricing(lang: str = "en") -> List[Dict[str, Any]]:
    if lang == "hi":
        path = DATA_DIR / "pricing_hi.json"
    else:
        path = DATA_DIR / "pricing.json"
    return load_json(path) if path.exists() else []


def load_faqs(lang: str = "en") -> List[Dict[str, str]]:
    if lang == "hi":
        path = DATA_DIR / "faqs_hi.json"
    else:
        path = DATA_DIR / "faqs.json"
    return load_json(path) if path.exists() else []


def load_testimonials(lang: str = "en") -> List[Dict[str, str]]:
    if lang == "hi":
        path = DATA_DIR / "testimonials_hi.json"
    else:
        path = DATA_DIR / "testimonials.json"
    return load_json(path) if path.exists() else []


def load_translations(lang: str) -> Dict[str, str]:
    if lang not in {"en", "hi"}:
        lang = "en"
    path = DATA_DIR / f"i18n_{lang}.json"
    if not path.exists():
        path = DATA_DIR / "i18n_en.json"
    return load_json(path)


def get_lang() -> str:
    lang = request.args.get("lang")
    if lang in {"en", "hi"}:
        return lang
    cookie_lang = request.cookies.get("lang")
    if cookie_lang in {"en", "hi"}:
        return cookie_lang
    return "en"


@app.after_request
def set_lang_cookie(resp):
    lang = request.args.get("lang")
    if lang in {"en", "hi"}:
        resp.set_cookie("lang", lang, max_age=60*60*24*365)
    return resp


@app.context_processor
def inject_seo_globals():
    path_only = request.path
    return {
        "site_url": SITE_URL.rstrip('/'),
        "canonical_url": f"{SITE_URL.rstrip('/')}{path_only}",
    }


@app.get("/")
def index():
    lang = get_lang()
    t = load_translations(lang)
    topics = load_topics(lang)
    pricing = load_pricing(lang)
    faqs = load_faqs(lang)
    testimonials = load_testimonials(lang)
    return render_template("index.html", t=t, topics=topics, pricing=pricing, faqs=faqs, testimonials=testimonials, lang=lang)


@app.get("/services")
def services():
    return redirect(url_for("index", _anchor="features"))


@app.get("/topics")
def topics_page():
    return redirect(url_for("index", _anchor="topics"))


@app.get("/pricing")
def pricing_page():
    return redirect(url_for("index", _anchor="pricing"))


@app.get("/faq")
def faq_page():
    return redirect(url_for("index", _anchor="faq"))


@app.get("/testimonials")
def testimonials_page():
    return redirect(url_for("index", _anchor="testimonials"))


@app.get("/contact")
def contact():
    lang = get_lang()
    t = load_translations(lang)
    topics = load_topics()
    return render_template("contact.html", t=t, topics=topics, lang=lang)


@app.post("/book")
def book():
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    email = (request.form.get("email") or "").strip()
    topic = (request.form.get("topic") or "").strip()
    message = (request.form.get("message") or "").strip()

    if not name or not phone or not topic:
        resp = {"ok": False, "error": "Missing required fields"}
        return jsonify(resp), 400

    is_new_file = not LEADS_CSV.exists()
    with LEADS_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow(["timestamp", "name", "phone", "email", "topic", "message", "ip"])
        writer.writerow([
            datetime.utcnow().isoformat(),
            name,
            phone,
            email,
            topic,
            message,
            request.headers.get("X-Forwarded-For", request.remote_addr or "")
        ])

    return jsonify({"ok": True})


@app.get("/guides")
def guides_list():
    lang = get_lang()
    t = load_translations(lang)
    guides = load_guides()
    return render_template("guides_list.html", t=t, lang=lang, guides=guides)


@app.get("/guides/<slug>")
def guide_detail(slug: str):
    lang = get_lang()
    t = load_translations(lang)
    guides = load_guides()
    guide = next((g for g in guides if g.get('slug') == slug), None)
    if not guide:
        abort(404)
    md_path = GUIDES_DIR / f"{slug}.md"
    if not md_path.exists():
        abort(404)
    with md_path.open("r", encoding="utf-8") as f:
        html = markdown(f.read(), extensions=['extra', 'sane_lists'])
    return render_template("guides_detail.html", t=t, lang=lang, guide=guide, content=html)


@app.get("/robots.txt")
def robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {SITE_URL.rstrip('/')}/sitemap.xml",
    ]
    resp = make_response("\n".join(lines))
    resp.headers["Content-Type"] = "text/plain"
    return resp


@app.get("/sitemap.xml")
def sitemap_xml():
    pages = [
        "/",
        "/contact",
        "/guides",
    ]
    for g in load_guides():
        pages.append(f"/guides/{g.get('slug')}")
    urlset = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
    ]
    for p in pages:
        loc = f"{SITE_URL.rstrip('/')}{p}"
        urlset.extend(["<url>", f"  <loc>{loc}</loc>", "</url>"])
    urlset.append("</urlset>")
    resp = make_response("\n".join(urlset))
    resp.headers["Content-Type"] = "application/xml"
    return resp


# Analytics API endpoints
@app.post("/api/log")
def log_event_api():
    """API endpoint to log events from frontend"""
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        metadata = data.get('metadata', {})
        
        if not event_type:
            return jsonify({"error": "event_type is required"}), 400
        
        log_event(event_type, session_id, user_id, metadata)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/analytics")
def get_analytics():
    """Get analytics data for admin dashboard"""
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        abort(401)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get event counts by type
    cursor.execute('''
        SELECT event_type, COUNT(*) as count 
        FROM events 
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY event_type
        ORDER BY count DESC
    ''')
    event_counts = [{"event_type": row[0], "count": row[1]} for row in cursor.fetchall()]
    
    # Get daily activity
    cursor.execute('''
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM events 
        WHERE timestamp >= datetime('now', '-30 days')
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    ''')
    daily_activity = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
    
    # Get progress stats
    cursor.execute('''
        SELECT lesson_id, COUNT(*) as completed_count
        FROM progress 
        WHERE completed = 1
        GROUP BY lesson_id
        ORDER BY completed_count DESC
    ''')
    progress_stats = [{"lesson_id": row[0], "completed_count": row[1]} for row in cursor.fetchall()]
    
    conn.close()
    
    # Check if CSV export is requested
    if request.args.get("format") == "csv":
        return export_analytics_csv(event_counts, daily_activity, progress_stats)
    
    return jsonify({
        "event_counts": event_counts,
        "daily_activity": daily_activity,
        "progress_stats": progress_stats
    })

def export_analytics_csv(event_counts, daily_activity, progress_stats):
    """Export analytics data as CSV"""
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write event counts
    writer.writerow(["Event Type", "Count (Last 7 Days)"])
    for item in event_counts:
        writer.writerow([item["event_type"], item["count"]])
    
    writer.writerow([])  # Empty row
    
    # Write daily activity
    writer.writerow(["Date", "Event Count"])
    for item in daily_activity:
        writer.writerow([item["date"], item["count"]])
    
    writer.writerow([])  # Empty row
    
    # Write progress stats
    writer.writerow(["Lesson ID", "Completed Count"])
    for item in progress_stats:
        writer.writerow([item["lesson_id"], item["completed_count"]])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=analytics_export.csv"
    return response

@app.post("/api/progress")
def update_progress():
    """Update lesson progress"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'anonymous')
        lesson_id = data.get('lesson_id')
        completed = data.get('completed', False)
        time_spent = data.get('time_spent', 0)
        
        if not lesson_id:
            return jsonify({"error": "lesson_id is required"}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO progress (user_id, lesson_id, completed, time_spent, timestamp)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, lesson_id, completed, time_spent))
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    lang = get_lang()
    t = load_translations(lang)
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == ADMIN_USERNAME and hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
            user = User("admin", username, ADMIN_PASSWORD_HASH)
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password", "error")
    
    return render_template("admin_login.html", t=t, lang=lang)

@app.route("/admin/logout")
@login_required
def admin_logout():
    """Admin logout"""
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("admin_login"))

@app.get("/admin/dashboard")
@login_required
def admin_dashboard():
    """Main admin dashboard"""
    lang = get_lang()
    t = load_translations(lang)
    return render_template("admin_dashboard.html", t=t, lang=lang, admin_token=ADMIN_TOKEN)

@app.get("/admin/analytics")
@login_required
def admin_analytics():
    """Analytics dashboard page"""
    lang = get_lang()
    t = load_translations(lang)
    return render_template("analytics.html", t=t, lang=lang, admin_token=ADMIN_TOKEN)

@app.get("/admin/leads")
def admin_leads():
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        abort(401)

    rows: List[List[str]] = []
    if LEADS_CSV.exists():
        with LEADS_CSV.open("r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
    else:
        rows = [["timestamp", "name", "phone", "email", "topic", "message", "ip"]]

    return render_template("leads.html", rows=rows)


if __name__ == "__main__":
    app.run(debug=True)
