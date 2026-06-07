import sqlite3
import os
from flask import g

DATA_DIR = os.environ.get("DATA_DIR", ".")
DATABASE = os.path.join(DATA_DIR, "record.db")

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)

def init_db(app):
    """Create the database and the tables if they don't exist."""
    with app.app_context():
        print(f"[init_db] DATA_DIR = {DATA_DIR}", flush=True)
        print(f"[init_db] DATABASE path = {DATABASE}", flush=True)
        print(f"[init_db] DATABASE exists: {os.path.exists(DATABASE)}", flush=True)
        print(f"[init_db] DATA_DIR exists: {os.path.exists(DATA_DIR)}", flush=True)
        print(f"[init_db] DATA_DIR is dir: {os.path.isdir(DATA_DIR)}", flush=True)
        if not os.path.exists(DATABASE):
            print(f"[init_db] Creating new database at {DATABASE}", flush=True)
            conn = sqlite3.connect(DATABASE)
            with open("schema.sql") as f:
                conn.executescript(f.read())
            conn.close()
            print(f"[init_db] Database created", flush=True)
        else:
            print(f"[init_db] Database already exists, skipping schema init", flush=True)