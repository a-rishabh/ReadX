# app/storage/db.py
import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "readx")
DB_USER = os.getenv("DB_USER", "readx")
DB_PASSWORD = os.getenv("DB_PASSWORD", "readx")

def _conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

@contextmanager
def get_conn():
    conn = _conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    ddl = """
    CREATE TABLE IF NOT EXISTS papers (
        id SERIAL PRIMARY KEY,
        filename TEXT NOT NULL,
        title TEXT,
        abstract TEXT,
        year INTEGER,
        venue TEXT,
        path TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS authors (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS paper_authors (
        paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
        author_id INTEGER REFERENCES authors(id) ON DELETE CASCADE,
        PRIMARY KEY (paper_id, author_id)
    );

    CREATE TABLE IF NOT EXISTS paper_chunks (
        id SERIAL PRIMARY KEY,
        paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
        section TEXT,
        chunk_index INTEGER,
        content TEXT
    );
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)

def insert_paper(filename, title, abstract, year, venue, path):
    sql = """
    INSERT INTO papers (filename, title, abstract, year, venue, path)
    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (filename, title, abstract, year, venue, path))
            return cur.fetchone()[0]

def upsert_author(name: str) -> int:
    sql = """
    INSERT INTO authors (name) VALUES (%s)
    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
    RETURNING id;
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (name,))
            return cur.fetchone()[0]

def link_paper_author(paper_id: int, author_id: int):
    sql = """
    INSERT INTO paper_authors (paper_id, author_id)
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING;
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (paper_id, author_id))

def insert_chunks(paper_id: int, chunks: list[tuple[str, str]]):
    """
    chunks: list of (section, content)
    """
    sql = """
    INSERT INTO paper_chunks (paper_id, section, chunk_index, content)
    VALUES (%s, %s, %s, %s);
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            for idx, (section, content) in enumerate(chunks):
                cur.execute(sql, (paper_id, section, idx, content))
