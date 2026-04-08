import sqlite3
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "gallery.db")
IMAGES_DIR = os.path.join(BASE_DIR, "public", "img")

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Включаем поддержку внешних ключей
    cursor.execute("PRAGMA foreign_keys = ON")

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    # Таблица авторов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bio TEXT,
            photo_url TEXT
        )
    ''')
    
    # Таблица коллекций (отдельные страницы)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            is_exhibition INTEGER DEFAULT 1
        )
    ''')
    
    # Таблица картин
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist_id INTEGER,
            price REAL,
            is_sold INTEGER DEFAULT 0,
            owner_id INTEGER DEFAULT NULL,
            image_id INTEGER,
            FOREIGN KEY (artist_id) REFERENCES artists (id),
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')

    # Таблица связей картин и коллекций (многие-ко-многим)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artwork_collection_map (
            artwork_id INTEGER,
            collection_id INTEGER,
            PRIMARY KEY (artwork_id, collection_id),
            FOREIGN KEY (artwork_id) REFERENCES artworks (id),
            FOREIGN KEY (collection_id) REFERENCES collections (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.get("/api/image/{art_id}")
async def get_image(art_id: int):
    file_path = os.path.join(IMAGES_DIR, f"{art_id}.jpg")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "Картина не найдена"}

app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)