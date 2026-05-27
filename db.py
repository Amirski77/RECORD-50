import sqlite3
import os
from flask import g

DATABASE = "record.db"

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
        if not os.path.exists(DATABASE):
            conn = sqlite3.connect(DATABASE)
            with open("schema.sql") as f:
                conn.executescript(f.read())
            conn.close()