import os, sqlite3
from pathlib import Path

DATA_DIR=Path(os.getenv("DATA_DIR","/data"))
DB_PATH=DATA_DIR/"revproxy.db"

SCHEMA="""
PRAGMA journal_mode=DELETE;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS management_acl (
 id INTEGER PRIMARY KEY, cidr TEXT UNIQUE NOT NULL, description TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS trusted_proxies (
 id INTEGER PRIMARY KEY, cidr TEXT UNIQUE NOT NULL, description TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS proxy_routes (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, path_prefix TEXT UNIQUE NOT NULL, upstream TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, add_x_forwarded INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS route_acl (
 id INTEGER PRIMARY KEY, route_id INTEGER NOT NULL REFERENCES proxy_routes(id) ON DELETE CASCADE, cidr TEXT NOT NULL, UNIQUE(route_id,cidr)
);
"""

def connect(readonly=False):
 DATA_DIR.mkdir(parents=True,exist_ok=True)
 if readonly and DB_PATH.exists():
  db=sqlite3.connect(f"file:{DB_PATH}?mode=ro",uri=True)
 else: db=sqlite3.connect(DB_PATH)
 db.row_factory=sqlite3.Row
 db.execute("PRAGMA foreign_keys=ON")
 db.execute("PRAGMA busy_timeout=3000")
 return db

def init_db():
 with connect() as db: db.executescript(SCHEMA)

def one(sql,args=()):
 with connect() as db: return db.execute(sql,args).fetchone()

def all(sql,args=()):
 with connect() as db: return db.execute(sql,args).fetchall()
