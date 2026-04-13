import sqlite3
import os
import bcrypt # Используем напрямую

db_path = os.path.join(os.path.dirname(__file__), "gallery.db")

def reset_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Пересоздаем таблицу
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')

    # Хешируем пароль "admin123" современным способом
    password = "admin123".encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password, salt).decode('utf-8')

    # Добавляем админа
    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                   ("admin", hashed_password, "admin"))

    conn.commit()
    conn.close()
    print("Таблица успешно пересоздана! Админ: admin / admin123")

if __name__ == "__main__":
    reset_db()