import os
import sqlite3
import bcrypt
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shutil
from fastapi.staticfiles import StaticFiles
import os
import uuid

def migrate_db():
    conn = sqlite3.connect('gallery.db')
    cursor = conn.cursor()
    # Добавляем колонку status, если её нет
    try:
        cursor.execute("ALTER TABLE purchase_requests ADD COLUMN status TEXT DEFAULT 'pending'")
    except sqlite3.OperationalError:
        pass 

    # ДОБАВЬТЕ ЭТО: Добавляем колонку bank_statement, если её нет
    try:
        cursor.execute("ALTER TABLE purchase_requests ADD COLUMN bank_statement TEXT")
        print("Колонка bank_statement успешно добавлена.")
    except sqlite3.OperationalError:
        print("Колонка bank_statement уже есть.")
        
    conn.commit()
    conn.close()

    
def get_db_connection():
 
    conn = sqlite3.connect('gallery.db')
    conn.row_factory = sqlite3.Row  # Это позволяет обращаться к полям по именам, а не по индексам
    return conn
if not os.path.exists("static/statements"):
    os.makedirs("static/statements", exist_ok=True)
app = FastAPI()
from fastapi.staticfiles import StaticFiles
# Создаем абсолютный путь к папке со статикой
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
upload_dir = os.path.join(BASE_DIR, "static", "statements")

if not os.path.exists(upload_dir):
    os.makedirs(upload_dir, exist_ok=True)

def fix_database_structure():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Проверяем наличие колонки bank_statement
        cursor.execute("SELECT bank_statement FROM purchase_requests LIMIT 1")
    except sqlite3.OperationalError:
        # Если колонки нет — добавляем её
        print("Добавляю колонку bank_statement в таблицу...")
        cursor.execute("ALTER TABLE purchase_requests ADD COLUMN bank_statement TEXT")
        conn.commit()
        print("Колонка успешно добавлена!")
    
    # На всякий случай проверим и status
    try:
        cursor.execute("SELECT status FROM purchase_requests LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE purchase_requests ADD COLUMN status TEXT DEFAULT 'pending'")
        conn.commit()
    
    conn.close()

# Вызываем функцию исправления
fix_database_structure()

# Монтируем статику, чтобы файлы были доступны по ссылке
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
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
                collection_id INTEGER,
                image_id INTEGER,
                is_sold INTEGER DEFAULT 0,
                FOREIGN KEY (artist_id) REFERENCES artists(id)
            )
        """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            artwork_id INTEGER,
            status TEXT DEFAULT 'pending',
            bank_statement TEXT, 
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (artwork_id) REFERENCES artworks(id)
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
    conn = get_db_connection()
    cursor = conn.cursor()
    # МЫ ДОБАВИЛИ "ar.name AS artist"
    cursor.execute('''
        SELECT a.id, a.title, a.price, a.is_sold, ar.name AS artist, 
               a.image_id, a.collection_id, u.username as owner
        FROM artworks a
        LEFT JOIN artists ar ON a.artist_id = ar.id
        LEFT JOIN purchase_requests r ON a.id = r.artwork_id AND r.status = 'approved'
        LEFT JOIN users u ON r.user_id = u.id
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"], 
            "title": r["title"], 
            "price": r["price"], 
            "is_sold": bool(r["is_sold"]), 
            "artist": r["artist"] or "Unknown", # Теперь этот ключ существует!
            "image_url": f"http://127.0.0.1:8000/api/image/{r['image_id']}", 
            "collection_id": r["collection_id"],
            "owner": r["owner"]
        } for r in rows
    ]


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

@app.get("/api/image/{image_id}")
async def get_image(image_id: str):
    image_path = os.path.join(BASE_DIR, "public", "img", f"{image_id}.jpg")
    if os.path.exists(image_path): return FileResponse(image_path)
    raise HTTPException(status_code=404)


@app.delete("/api/collections/{col_id}")
async def delete_collection(col_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM collections WHERE id = ?", (col_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Коллекция не найдена")
    
    try:
        cursor.execute("UPDATE artworks SET collection_id = NULL WHERE collection_id = ?", (col_id,))
        
        cursor.execute("DELETE FROM collections WHERE id = ?", (col_id,))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        print(f"Ошибка при удалении коллекции: {e}")
        raise HTTPException(status_code=500, detail="Ошибка базы данных при удалении")
    finally:
        conn.close()

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
    
@app.delete("/api/purchase-requests/{request_id}")
async def reject_request(request_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM purchase_requests WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()
    return {"status": "rejected"}

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


class PurchaseRequestData(BaseModel):
    user_id: int
    artwork_id: int

@app.post("/api/purchase-requests")
async def create_purchase_request(
    user_id: int = Form(...), 
    artwork_id: int = Form(...), 
    file: UploadFile = File(...)
):
    upload_dir = "static/statements"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
        
    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    file_url = f"http://127.0.0.1:8000/static/statements/{safe_filename}"
    
    # ИСПРАВЛЕНО: явно указываем 4 колонки, чтобы не было конфликта
    cursor.execute(
        "INSERT INTO purchase_requests (user_id, artwork_id, bank_statement, status) VALUES (?, ?, ?, ?)",
        (user_id, artwork_id, file_url, 'pending')
    )
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "Заявка принята"}
@app.get("/api/purchase-requests")
async def get_purchase_requests():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Добавь r.bank_statement в SELECT
    cursor.execute("""
        SELECT r.id, u.username, a.title as artwork_title, a.price, r.bank_statement 
        FROM purchase_requests r
        JOIN users u ON r.user_id = u.id
        JOIN artworks a ON r.artwork_id = a.id
        WHERE r.status = 'pending'
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/api/purchase-requests/{request_id}/approve")
async def approve_purchase_request(request_id: int):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Ищем картину
    cursor.execute("SELECT artwork_id FROM purchase_requests WHERE id = ?", (request_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return {"error": "Заявка не найдена"}, 404
        
    artwork_id = row["artwork_id"]

    # Обновляем картину и статусы заявок
    cursor.execute("UPDATE artworks SET is_sold = 1 WHERE id = ?", (artwork_id,))
    cursor.execute("UPDATE purchase_requests SET status = 'approved' WHERE id = ?", (request_id,))
    cursor.execute("UPDATE purchase_requests SET status = 'rejected' WHERE artwork_id = ? AND id != ?", (artwork_id, request_id))
    
    conn.commit()
    conn.close()
    return {"message": "Success"}


@app.get("/api/my-collection/{user_id}")
async def get_my_collection(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Запрос находит картины, где статус заявки данного пользователя 'approved'
    cursor.execute("""
        SELECT a.id, a.title, a.price, a.image_id, ar.name AS artist
        FROM artworks a
        JOIN purchase_requests r ON a.id = r.artwork_id
        JOIN artists ar ON a.artist_id = ar.id
        WHERE r.user_id = ? AND r.status = 'approved'
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r["id"], 
            "title": r["title"], 
            "price": r["price"],
            "artist": r["artist"],
            "image_url": f"http://127.0.0.1:8000/api/image/{r['image_id']}"
        } for r in rows
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)