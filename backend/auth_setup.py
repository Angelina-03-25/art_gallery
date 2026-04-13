import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    conn = sqlite3.connect("gallery.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')
    # Добавим админа для теста
    hashed_pass = pwd_context.hash("admin123")
    try:
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       ("admin", hashed_pass, "admin"))
        conn.commit()
    except: pass
    conn.close()

if __name__ == "__main__":
    init_db()
    print("База данных готова к работе с пользователями.")