from flask import Flask, render_template, request, redirect, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import db
import os
from db import get_db
from functools import wraps
from datetime import datetime, timezone, date, timedelta

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
db.init_app(app)
db.init_db(app)

def display_streak(current_streak, last_post_date_str):
    if not last_post_date_str:
        return 0
    last = date.fromisoformat(last_post_date_str)
    today = datetime.now(timezone.utc).date()
    if last == today or last == today - timedelta(days=1):
        return current_streak
    return 0

@app.route("/")
def index():
    if "user_id" not in session:
        return render_template("index.html")

    conn = get_db()
    today_utc = datetime.now(timezone.utc).date().isoformat()

    posts = conn.execute(
        """
        SELECT posts.id, posts.track_name, posts.artist_name, posts.album_art_url, posts.preview_url, posts.note, posts.created_at, users.username
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE DATE(posts.created_at) = ?
        ORDER BY posts.created_at DESC
        """,
        (today_utc,),
    ).fetchall()

    user_posted_today = any(p["username"] == session["username"] for p in posts)

    return render_template("index.html", posts=posts, user_posted_today=user_posted_today)
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required")
            return redirect("/register")
        
        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()

        if existing:
            flash("Username already exists")
            return redirect("/register")

        password_hash = generate_password_hash(password)
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()

        session["user_id"] = cursor.lastrowid
        session["username"] = username
        flash("Account created successfully")
        return redirect("/")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required")
            return redirect("/login")

        conn = get_db()
        user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?", (username,),
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password")
            return redirect("/login")

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash("Logged in successfully")
        return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out")
    return redirect("/")

@app.route("/api/search")
def search():
    query = request.args.get("q", "").strip()[:100]

    if not query:
        return jsonify({"results": []})

    try:
        response = requests.get("https://itunes.apple.com/search",
        params={
            "term": query, 
            "media": "music",
            "entity": "song", 
            "limit": 25,
        },
        timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return jsonify({"results": []}), 502

    results = []
    for track in data.get("results", []):
        results.append({
            "track_id": track.get("trackId"),
            "track_name": track.get("trackName"),
            "artist_name": track.get("artistName"),
            "album_art_url": track.get("artworkUrl100"),
            "preview_url": track.get("previewUrl"),
        })

    return jsonify({"results": results})

@app.route("/search")
@login_required
def search_page():
    return render_template("search.html")

@app.route("/post", methods=["POST"])
@login_required
def post_record():
    track_id = request.form.get("track_id", "").strip()
    track_name = request.form.get("track_name", "").strip()
    artist_name = request.form.get("artist_name", "").strip()
    album_art_url = request.form.get("album_art_url", "").strip()
    preview_url = request.form.get("preview_url", "").strip() or None
    note = request.form.get("note", "").strip()

    if not (track_id and track_name and artist_name and album_art_url):
        flash("Missing track info - pick a song first")
        return redirect("/search")

    if len(note) > 280:
        flash("Note too long (max 280 characters).")
        return redirect("/search")

    conn = get_db()

    today_utc = datetime.now(timezone.utc).date().isoformat()
    already_posted = conn.execute(
        "SELECT id FROM posts WHERE user_id = ? AND DATE(created_at) = ?",
        (session["user_id"], today_utc),
    ).fetchone()

    if already_posted:
        flash("You've already posted a song today. Come back tomorrow!")
        return redirect("/search")

    conn.execute(
        """
        INSERT INTO posts (user_id, track_id, track_name, artist_name, album_art_url, preview_url, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"], 
            track_id, 
            track_name, 
            artist_name, 
            album_art_url, 
            preview_url, 
            note or None,
        ),
    )

    #streak update
    today = datetime.now(timezone.utc).date()
    user = conn.execute(
        "SELECT current_streak, last_post_date FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()

    last = date.fromisoformat(user["last_post_date"]) if user["last_post_date"] else None
    
    if last == today - timedelta(days=1):
        new_streak = user["current_streak"] + 1
    else:
        new_streak = 1

    conn.execute(
        "UPDATE users SET current_streak = ?, last_post_date = ? WHERE id = ?",
        (new_streak, today.isoformat(), session["user_id"]),
    )
    conn.commit()

    if new_streak == 1:
        flash("Your record is posted! 🔥 Day 1 - the streak begins.")
    else:
        flash(f"Your record is posted! 🔥 Day {new_streak} - streak alive!")

    return redirect("/")

@app.route("/user/<username>")
def profile(username):
    conn = get_db()

    user = conn.execute(
        "SELECT id, username, created_at FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if user is None:
        flash("User not found")
        return redirect("/")

    posts = conn.execute(
        """
        SELECT id, track_name, artist_name, album_art_url, preview_url, note, created_at 
        FROM posts 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        """,
        (user["id"],),
    ).fetchall()

    return render_template("profile.html", profile_user=user, posts=posts)