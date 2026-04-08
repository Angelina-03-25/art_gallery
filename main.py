import sqlite3
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "gallery.db")
IMAGES_DIR = os.path.join(BASE_DIR, "public", "img")

# Блок инициализации базы данных
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Создание таблицы авторов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bio TEXT,
            photo_url TEXT
        )
    ''')
    
    # Создание таблицы картин с учетом коллекций и статуса продажи
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist_id INTEGER,
            price REAL,
            collection TEXT,
            is_sold INTEGER DEFAULT 0,
            image_id INTEGER,
            FOREIGN KEY (artist_id) REFERENCES artists (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Запуск инициализации при старте
init_db()

# Блок обработки запросов к изображениям
@app.get("/api/image/{art_id}")
async def get_image(art_id: int):
    file_path = os.path.join(IMAGES_DIR, f"{art_id}.jpg")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "Картина не найдена"}

# Блок подключения фронтенда
app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)