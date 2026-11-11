from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "loksanskriti.db"

app = FastAPI(title="LokSanskriti API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS traditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        state TEXT NOT NULL,
        district TEXT,
        language TEXT,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        history TEXT,
        emoji TEXT DEFAULT '🇮🇳'
    )
    """)
    count = conn.execute("SELECT COUNT(*) FROM traditions").fetchone()[0]
    if count == 0:
        seed = [
            ("Sohar", "Bihar", "West Champaran", "Bhojpuri", "Folk Song",
             "Traditional songs associated with celebrations surrounding childbirth.",
             "An oral folk tradition passed through generations.", "🎵"),
            ("Bihu Traditions", "Assam", "Kamrup", "Assamese", "Festival",
             "Songs, dance, instruments and customs connected with Bihu celebrations.",
             "A major part of Assamese cultural life.", "🪘"),
            ("Kathputli", "Rajasthan", "Jaipur", "Rajasthani", "Folk Story",
             "Traditional storytelling through puppetry, music and performance.",
             "A long-standing Rajasthani puppetry tradition.", "🎭"),
            ("Madhubani Folk Art", "Bihar", "Madhubani", "Maithili", "Craft",
             "A distinctive painting tradition known for symbolic motifs and natural themes.",
             "A major folk-art tradition of the Mithila region.", "🎨"),
            ("Chhau Dance", "Odisha", "Mayurbhanj", "Odia", "Folk Dance",
             "A powerful traditional dance form combining movement, music and storytelling.",
             "A major eastern Indian performance tradition.", "💃"),
            ("Baul Music", "West Bengal", "Birbhum", "Bengali", "Folk Music",
             "Mystical folk music centered on spiritual and humanistic themes.",
             "A distinctive oral musical tradition of Bengal.", "🎶"),
        ]
        conn.executemany("""
            INSERT INTO traditions
            (name,state,district,language,category,description,history,emoji)
            VALUES (?,?,?,?,?,?,?,?)
        """, seed)
    conn.commit()
    conn.close()

init_db()

class TraditionCreate(BaseModel):
    name: str
    state: str
    district: str = ""
    language: str = ""
    category: str
    description: str
    history: str = ""
    emoji: str = "🇮🇳"

@app.get("/")
def root():
    return {"message": "LokSanskriti API is running", "docs": "/docs"}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/stats")
def stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM traditions").fetchone()[0]
    states = conn.execute("SELECT COUNT(DISTINCT state) FROM traditions").fetchone()[0]
    categories = conn.execute("SELECT COUNT(DISTINCT category) FROM traditions").fetchone()[0]
    conn.close()
    return {"traditions": total, "states": states, "categories": categories, "priority": 3}

@app.get("/api/traditions")
def traditions(search: str = "", state: str = "", category: str = ""):
    conn = get_db()
    sql = "SELECT * FROM traditions WHERE 1=1"
    params = []
    if search:
        sql += """ AND (name LIKE ? OR state LIKE ? OR language LIKE ?
                   OR category LIKE ? OR description LIKE ?)"""
        q = f"%{search}%"
        params += [q, q, q, q, q]
    if state:
        sql += " AND state = ?"
        params.append(state)
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY id DESC"
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    return rows

@app.get("/api/traditions/{tradition_id}")
def tradition(tradition_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM traditions WHERE id=?", (tradition_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Tradition not found")
    return dict(row)

@app.post("/api/traditions", status_code=201)
def create_tradition(item: TraditionCreate):
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO traditions
        (name,state,district,language,category,description,history,emoji)
        VALUES (?,?,?,?,?,?,?,?)
    """, tuple(item.model_dump().values()))
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM traditions WHERE id=?", (new_id,)).fetchone()
    conn.close()
    return dict(row)
