import psycopg2
from contextlib import contextmanager
from config import DATABASE_URL

@contextmanager
def get_cursor():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
