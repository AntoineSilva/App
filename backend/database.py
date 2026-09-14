"""
Gestion de la base de données SQLite : chaque ligne est une recherche créée
depuis l'app mobile, rattachée au push_token (identifiant unique) du
téléphone qui l'a créée.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).parent / "vinted_app.db"


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                push_token TEXT NOT NULL,
                nom TEXT NOT NULL,
                mots_cles TEXT NOT NULL,
                prix_min REAL,
                prix_max REAL,
                marque TEXT,
                taille TEXT,
                actif INTEGER DEFAULT 1,
                derniers_ids TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def add_search(push_token, nom, mots_cles, prix_min=None, prix_max=None, marque=None, taille=None):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute(
            """INSERT INTO searches (push_token, nom, mots_cles, prix_min, prix_max, marque, taille)
               VALUES (?,?,?,?,?,?,?)""",
            (push_token, nom, mots_cles, prix_min, prix_max, marque, taille),
        )
        conn.commit()
        return cur.lastrowid


def list_searches(push_token):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM searches WHERE push_token=? AND actif=1 ORDER BY id", (push_token,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_active_searches():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM searches WHERE actif=1").fetchall()
        return [dict(r) for r in rows]


def remove_search(push_token, search_id):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute(
            "UPDATE searches SET actif=0 WHERE id=? AND push_token=?", (search_id, push_token)
        )
        conn.commit()
        return cur.rowcount > 0


def update_seen_ids(search_id, ids_csv):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("UPDATE searches SET derniers_ids=? WHERE id=?", (ids_csv, search_id))
        conn.commit()
