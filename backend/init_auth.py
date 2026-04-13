import sqlite3
# Для защиты паролей (установи: pip install passlib)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
conn = sqlite3.connect("gallery.db")
cursor = conn.cursor()

# Создаем таблицу пользователей
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user' -- roles: guest, user, admin
    )
''')

# Добавим тестового админа (пароль: admin123)
admin_pass = pwd_context.hash("admin123")
try:
    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                   ("admin", admin_pass, "admin"))
    conn.commit()
    print("Таблица создана, админ добавлен.")
except:
    print("Админ уже существует.")
conn.close()