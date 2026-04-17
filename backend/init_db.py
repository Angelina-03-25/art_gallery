# import sqlite3

# # Укажите путь к вашему файлу базы данных
# DATABASE_PATH = 'database.db' 

# def update_db():
#     conn = sqlite3.connect(DATABASE_PATH)
#     cursor = conn.cursor()

#     try:
#         # 1. Создаем таблицу связей "Многие-ко-многим"
#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS artwork_collections (
#                 artwork_id INTEGER,
#                 collection_id INTEGER,
#                 FOREIGN KEY (artwork_id) REFERENCES artworks(id),
#                 FOREIGN KEY (collection_id) REFERENCES collections(id)
#             )
#         """)
        
#         conn.commit()
#         print("База данных успешно обновлена: таблица связей создана.")
#     except Exception as e:
#         print(f"Произошла ошибка: {e}")
#     finally:
#         conn.close()

# if __name__ == "__main__":
#     update_db()

import sqlite3
import bcrypt
import os

DATABASE_PATH = "gallery.db"

def setup_complete_db():
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 1. СОЗДАНИЕ СТРУКТУРЫ
    cursor.execute("CREATE TABLE artists (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
    cursor.execute("CREATE TABLE collections (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, description TEXT)")
    cursor.execute("""
        CREATE TABLE artworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price INTEGER,
            artist_id INTEGER,
            collection_id INTEGER,
            image_id INTEGER,
            is_sold INTEGER DEFAULT 0,
            FOREIGN KEY (artist_id) REFERENCES artists(id),
            FOREIGN KEY (collection_id) REFERENCES collections(id)
        )
    """)
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT, role TEXT)")

    # 2. ДОБАВЛЕНИЕ АДМИНА (admin / 123)
    pwd = "123".encode('utf-8')
    hashed = bcrypt.hashpw(pwd, bcrypt.gensalt()).decode('utf-8')
    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', hashed, 'admin'))

    # 3. ПОДГОТОВКА ДАННЫХ
    # Формат: (Название, Автор, Примерная цена в $)
    raw_data = [
        ("Мона Лиза", "Леонардо да Винчи", 860000000),
        ("Сикстинская мадонна", "Рафаэль", 150000000),
        ("Девушка с жемчужной серёжкой", "Ян Вермеер", 30000000),
        ("Свобода, ведущая народ", "Эжен Делакруа", 45000000),
        ("Дама с горностаем", "Леонардо да Винчи", 90000000),
        ("Ночной дозор", "Рембрандт", 100000000),
        ("Тайная вечеря", "Леонардо да Винчи", 450000000),
        ("Спаситель Мира (Сальватор Мунди)", "Леонардо да Винчи", 450300000),
        ("Девятый вал", "Иван Айвазовский", 5000000),
        ("Неизвестная", "Иван Крамской", 3000000),
        ("Похищение Прозерпины", "Алессандро Аллори", 12000000),
        ("Сын человеческий", "Рене Магритт", 25000000),
        ("Утро в сосновом лесу", "Шишкин и Савицкий", 4000000),
        ("Вспаханное поле и пахарь", "Винсент Ван Гог", 80000000),
        ("Влюбленные", "Рене Магритт", 15000000),
        ("Рождение Венеры", "Сандро Боттичелли", 150000000),
        ("Иван-Царевич на Сером Волке", "Виктор Васнецов", 8000000),
        ("Алёнушка", "Виктор Васнецов", 7000000),
        ("Чёрный супрематический квадрат", "Казимир Малевич", 20000000),
        ("Подсолнухи", "Винсент Ван Гог", 75000000)
    ]

    cursor.execute("INSERT INTO collections (name, description) VALUES (?, ?)", ("Шедевры мирового искусства", "Основные экспонаты галереи"))
    col_id = cursor.lastrowid

    # 4. ЦИКЛ ЗАПОЛНЕНИЯ
    for idx, (title, artist_name, price) in enumerate(raw_data, start=1):
        cursor.execute("INSERT OR IGNORE INTO artists (name) VALUES (?)", (artist_name,))
        cursor.execute("SELECT id FROM artists WHERE name = ?", (artist_name,))
        art_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO artworks (title, price, artist_id, collection_id, image_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (title, price, art_id, col_id, idx))

    conn.commit()
    conn.close()
    print(f"База данных создана! Добавлено {len(raw_data)} картин.")
    print("Доступ: admin / 123")

if __name__ == "__main__":
    setup_complete_db()