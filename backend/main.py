import os
import sqlite3
import bcrypt
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "gallery.db")

# Инициализация БД 
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    

    cursor.execute("CREATE TABLE IF NOT EXISTS artists (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT UNIQUE, 
            password_hash TEXT, 
            role TEXT
        )
    """)
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    """)
    
    # Таблица картин
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price INTEGER,
            artist_id INTEGER,
            image_id INTEGER,
            is_sold INTEGER DEFAULT 0,
            FOREIGN KEY (artist_id) REFERENCES artists(id)
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artwork_collections (
            artwork_id INTEGER,
            collection_id INTEGER,
            FOREIGN KEY (artwork_id) REFERENCES artworks(id),
            FOREIGN KEY (collection_id) REFERENCES collections(id)
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

class AuthData(BaseModel):
    username: str
    password: str

#  Эндпоинты авторов 
@app.post("/api/artists")
async def add_artist(data: dict):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO artists (name) VALUES (?)", (data['name'],))
    conn.commit()
    res = {"status": "success", "id": cursor.lastrowid}
    conn.close()
    return res

@app.get("/api/artists")
async def get_artists():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM artists")
    artists = cursor.fetchall()
    conn.close()
    return [{"id": a[0], "name": a[1]} for a in artists]

# Эндпоинты картин 
@app.post("/api/artworks")
async def add_artwork(
    title: str = Form(...),
    price: int = Form(...),
    artist_id: int = Form(...),
    collection_id: int = Form(None), # Убедись, что тут написано collection_id
    image: UploadFile = File(...)
):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(id) FROM artworks")
        max_id = cursor.fetchone()[0] or 0
        new_id = max_id + 1
        
        # Сохранение фото
        img_dir = os.path.join(BASE_DIR, "public", "img")
        os.makedirs(img_dir, exist_ok=True)
        file_location = os.path.join(img_dir, f"{new_id}.jpg")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        # Запись в базу (БЕЗ json.loads)
        cursor.execute('''
            INSERT INTO artworks (title, price, artist_id, collection_id, image_id, is_sold) 
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (title, price, artist_id, collection_id, new_id))
        
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении")
    finally:
        conn.close()

@app.get("/api/artworks")
async def get_artworks():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.id, a.title, a.price, a.is_sold, ar.name, a.image_id, a.collection_id
        FROM artworks a
        LEFT JOIN artists ar ON a.artist_id = ar.id
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "title": r[1], "price": r[2], 
            "is_sold": bool(r[3]), "artist": r[4] or "Unknown", 
            "image_url": f"http://127.0.0.1:8000/api/image/{r[5]}", "collection_id": r[6]
        } for r in rows
    ]

# Эндпоинты коллекций 
@app.post("/api/collections")
async def create_collection(data: dict):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:

        cursor.execute("INSERT INTO collections (name, description) VALUES (?, ?)", 
                       (data['name'], data.get('description', '')))
        col_id = cursor.lastrowid
        

        if data.get('artwork_ids'):
            for art_id in data['artwork_ids']:
                cursor.execute("INSERT INTO artwork_collections (artwork_id, collection_id) VALUES (?, ?)", 
                               (art_id, col_id))
        conn.commit()
        return {"status": "success", "id": col_id}
    finally:
        conn.close()

        

@app.get("/api/collections")
async def get_collections():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM collections")
    cols = cursor.fetchall()
    conn.close()
    return [{"id": c[0], "name": c[1], "description": c[2]} for c in cols]

#  Авторизация 
@app.post("/api/register")
async def register(data: AuthData):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        hashed = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       (data.username, hashed, "user"))
        conn.commit()
        return {"status": "success"}
    except:
        raise HTTPException(status_code=400, detail="Логин занят")
    finally:
        conn.close()

@app.post("/api/login")
async def login(data: AuthData):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (data.username,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(data.password.encode('utf-8'), user[2].encode('utf-8')):
        return {"status": "success", "user": {"id": user[0], "username": user[1], "role": user[3]}}
    raise HTTPException(status_code=401, detail="Ошибка входа")

# --- Остальные функции (удаление, изображения) ---
@app.get("/api/image/{image_id}")
async def get_image(image_id: str):
    image_path = os.path.join(BASE_DIR, "public", "img", f"{image_id}.jpg")
    if os.path.exists(image_path): return FileResponse(image_path)
    raise HTTPException(status_code=404)


@app.delete("/api/collections/{col_id}")
async def delete_collection(col_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # Проверяем существование
    cursor.execute("SELECT id FROM collections WHERE id = ?", (col_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Коллекция не найдена")
    

    cursor.execute("DELETE FROM artwork_collections WHERE collection_id = ?", (col_id,))
    cursor.execute("DELETE FROM collections WHERE id = ?", (col_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

#  Добавление существующей картины в коллекцию
@app.post("/api/collections/assign")
async def assign_art_to_collection(data: dict):

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:

        cursor.execute("""
            INSERT OR IGNORE INTO artwork_collections (artwork_id, collection_id) 
            VALUES (?, ?)
        """, (data['artwork_id'], data['collection_id']))
        conn.commit()
        return {"status": "assigned"}
    finally:
        conn.close()

@app.get("/api/users")
async def get_users():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    conn.close()
    return [{"id": u[0], "username": u[1], "role": u[2]} for u in users]

@app.put("/api/artworks/{art_id}")
async def update_artwork(art_id: int, data: dict):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:

        cursor.execute("SELECT id FROM artworks WHERE id = ?", (art_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Картина не найдена")


        cursor.execute('''
            UPDATE artworks 
            SET title = ?, price = ?, artist_id = ?, collection_id = ?
            WHERE id = ?
        ''', (
            data.get('title'), 
            data.get('price'), 
            data.get('artist_id'), 
            data.get('collection_id'), 
            art_id
        ))
        
        conn.commit()
        return {"status": "success", "message": f"Artwork {art_id} updated"}
    except Exception as e:
        print(f"Update error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении базы данных")
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)