
import os
import sqlite3
import time
import hmac
import hashlib
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(title="LokSanskriti API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "loksanskriti.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            state TEXT NOT NULL,
            district TEXT,
            language TEXT,
            category TEXT,
            description TEXT NOT NULL,
            history TEXT,
            emoji TEXT
        )
    """)

    columns = [
        row["name"]
        for row in cursor.execute("PRAGMA table_info(traditions)").fetchall()
    ]

    if "approved" not in columns:
        cursor.execute("""
            ALTER TABLE traditions
            ADD COLUMN approved INTEGER NOT NULL DEFAULT 1
        """)

    count = cursor.execute(
        "SELECT COUNT(*) FROM traditions"
    ).fetchone()[0]

    if count == 0:
        seeds = [
            ("Baul Music", "West Bengal", "", "Bengali", "Folk Music",
             "Baul music is a traditional spiritual folk music of Bengal.",
             "It is associated with wandering mystic singers.", "🎵", 1),

            ("Chhau Dance", "Odisha", "", "Odia", "Folk Dance",
             "Chhau is a traditional dance form combining martial movements and storytelling.",
             "It is performed during festivals and cultural celebrations.", "💃", 1),

            ("Madhubani Folk Art", "Bihar", "", "Maithili", "Craft",
             "Madhubani painting is a traditional art form known for its colourful patterns.",
             "It originated in the Mithila region of Bihar.", "🎨", 1),

            ("Kathputli", "Rajasthan", "", "Rajasthani", "Folk Story",
             "Kathputli is a traditional Rajasthani string puppet performance.",
             "It has been used to tell stories for generations.", "🪆", 1),

            ("Bihu Traditions", "Assam", "", "Assamese", "Festival",
             "Bihu is a major cultural festival of Assam.",
             "It celebrates the agricultural seasons and Assamese culture.", "🌾", 1),

            ("Sohar", "Bihar", "", "Bhojpuri", "Folk Song",
             "Sohar is a traditional folk song sung during childbirth celebrations.",
             "It is an important part of family and community traditions.", "🎶", 1),
        ]

        cursor.executemany("""
            INSERT INTO traditions
            (name, state, district, language, category, description,
             history, emoji, approved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seeds)

    conn.commit()
    conn.close()


init_db()


class TraditionCreate(BaseModel):
    name: str
    state: str
    district: Optional[str] = ""
    language: Optional[str] = ""
    category: Optional[str] = ""
    description: str
    history: Optional[str] = ""
    emoji: Optional[str] = "🏛️"


def admin_token(password: str):
    secret = os.getenv("ADMIN_SECRET_KEY")
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="Admin secret key is not configured."
        )

    expiry = str(int(time.time()) + 43200)
    message = f"{password}:{expiry}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{expiry}.{signature}"


def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    password = os.getenv("ADMIN_PASSWORD")
    secret = os.getenv("ADMIN_SECRET_KEY")

    if not password or not secret:
        raise HTTPException(
            status_code=503,
            detail="Admin credentials are not configured."
        )

    if not x_admin_token or "." not in x_admin_token:
        raise HTTPException(status_code=401, detail="Admin login required.")

    try:
        expiry, supplied_signature = x_admin_token.split(".", 1)
        if int(expiry) < int(time.time()):
            raise HTTPException(status_code=401, detail="Admin session expired.")

        message = f"{password}:{expiry}"
        expected_signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise HTTPException(status_code=401, detail="Invalid admin token.")

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid admin token.")

    return True


@app.get("/")
def home():
    return {
        "message": "LokSanskriti API is running",
        "docs": "/docs"
    }


@app.get("/api/health")
def health():
    return {"status": "healthy"}


@app.get("/api/stats")
def get_stats():
    conn = get_db()
    cursor = conn.cursor()

    traditions = cursor.execute(
        "SELECT COUNT(*) FROM traditions WHERE approved = 1"
    ).fetchone()[0]

    states = cursor.execute(
        "SELECT COUNT(DISTINCT state) FROM traditions WHERE approved = 1"
    ).fetchone()[0]

    categories = cursor.execute(
        "SELECT COUNT(DISTINCT category) FROM traditions WHERE approved = 1"
    ).fetchone()[0]

    conn.close()

    return {
        "traditions": traditions,
        "states": states,
        "categories": categories,
        "priority": 3
    }


@app.get("/api/traditions")
def get_traditions(
    search: Optional[str] = None,
    state: Optional[str] = None
):
    conn = get_db()
    query = "SELECT * FROM traditions WHERE approved = 1"
    params = []

    if search:
        query += """
            AND (
                name LIKE ? OR
                description LIKE ? OR
                category LIKE ? OR
                state LIKE ?
            )
        """
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if state:
        query += " AND state = ?"
        params.append(state)

    query += " ORDER BY id DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/api/traditions/{tradition_id}")
def get_tradition(tradition_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM traditions WHERE id = ? AND approved = 1",
        (tradition_id,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Tradition not found")

    return dict(row)


@app.post("/api/traditions")
def add_tradition(tradition: TraditionCreate):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO traditions
        (name, state, district, language, category, description,
         history, emoji, approved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        tradition.name,
        tradition.state,
        tradition.district,
        tradition.language,
        tradition.category,
        tradition.description,
        tradition.history,
        tradition.emoji
    ))

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "message": "Contribution submitted for admin approval.",
        "id": new_id
    }


@app.post("/api/admin/login")
def admin_login(data: dict):
    correct_password = os.getenv("ADMIN_PASSWORD")

    if not correct_password or not os.getenv("ADMIN_SECRET_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Admin credentials are not configured on the server."
        )

    supplied_password = data.get("password", "")

    if not hmac.compare_digest(str(supplied_password), correct_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {
        "message": "Admin login successful",
        "token": admin_token(correct_password)
    }


@app.get("/api/admin/traditions")
def admin_get_traditions(
    admin: bool = Depends(require_admin)
):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM traditions ORDER BY approved ASC, id DESC"
    ).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.patch("/api/admin/traditions/{tradition_id}/approve")
def approve_tradition(
    tradition_id: int,
    admin: bool = Depends(require_admin)
):
    conn = get_db()

    cursor = conn.execute(
        "UPDATE traditions SET approved = 1 WHERE id = ?",
        (tradition_id,)
    )

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Tradition not found")

    return {"message": "Contribution approved successfully"}


@app.delete("/api/admin/traditions/{tradition_id}")
def delete_tradition(
    tradition_id: int,
    admin: bool = Depends(require_admin)
):
    conn = get_db()

    cursor = conn.execute(
        "DELETE FROM traditions WHERE id = ?",
        (tradition_id,)
    )

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Tradition not found")

    return {"message": "Tradition deleted successfully"}
