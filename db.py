import sqlite3

def get_db_connection():
    conn = sqlite3.connect('football_app.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with open('schema.sql', 'r') as fute:
        conn.executescript(fute.read())
    conn.commit()
    conn.close()
