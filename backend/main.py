import os
import sqlite3
import bcrypt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi import UploadFile, File, Form
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

class AuthData(BaseModel):
    username: str
    password: str

# 1. Добавление нового автора
@app.post("/api/artists")
async def add_artist(data: dict):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO artists (name) VALUES (?)", (data['name'],))
        conn.commit()
        return {"status": "success", "id": cursor.lastrowid}
    finally:
        conn.close()

# 2. Получение списка всех авторов
@app.get("/api/artists")
async def get_artists():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM artists")
    artists = cursor.fetchall()
    conn.close()
    return [{"id": a[0], "name": a[1]} for a in artists]

# 3. Редактирование картины (название, цена, автор)
@app.put("/api/artworks/{art_id}")
async def update_artwork(art_id: int, data: dict):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE artworks 
            SET title = ?, price = ?, artist_id = ? 
            WHERE id = ?
        ''', (data['title'], data['price'], data['artist_id'], art_id))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
        
# ДОБАВЛЕНИЕ НОВОЙ КАРТИНЫ
@app.post("/api/artworks")
async def add_artwork(
    title: str = Form(...),
    price: int = Form(...),
    artist_id: int = Form(...),
    image: UploadFile = File(...)
):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        # 1. Генерируем ID для изображения (возьмем следующий по счету)
        cursor.execute("SELECT MAX(id) FROM artworks")
        max_id = cursor.fetchone()[0] or 0
        new_image_id = max_id + 1
        
        # 2. Сохраняем файл в папку public/img
        file_location = os.path.join(BASE_DIR, "public", "img", f"{new_image_id}.jpg")
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        # 3. Записываем данные в БД
        cursor.execute('''
            INSERT INTO artworks (title, price, artist_id, image_id, is_sold) 
            VALUES (?, ?, ?, ?, 0)
        ''', (title, price, artist_id, new_image_id))
        
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        print(f"Error adding art: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении картины")
    finally:
        conn.close()

# ЭНДПОИНТ РЕГИСТРАЦИИ
@app.post("/api/register")
async def register(data: AuthData):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        # Проверяем, нет ли уже такого пользователя
        cursor.execute("SELECT id FROM users WHERE username = ?", (data.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Этот логин уже занят")

        # Хешируем пароль
        password_bytes = data.password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        # Сохраняем (роль по умолчанию 'user')
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       (data.username, hashed, "user"))
        conn.commit()
        return {"status": "success", "message": "User created"}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    finally:
        conn.close()

# ЭНДПОИНТ ВХОДА (уже знакомый нам)
@app.post("/api/login")
async def login(data: AuthData):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (data.username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        stored_hash = user[2].encode('utf-8')
        user_password = data.password.encode('utf-8')
        if bcrypt.checkpw(user_password, stored_hash):
            return {
                "status": "success",
                "user": {"id": user[0], "username": user[1], "role": user[3]}
            }
    
    raise HTTPException(status_code=401, detail="Неверный логин или пароль")

# (Остальные эндпоинты /api/artworks и /api/image оставь без изменений)
@app.get("/api/artworks")
async def get_artworks():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, a.title, a.price, a.is_sold, ar.name, a.image_id
            FROM artworks a
            LEFT JOIN artists ar ON a.artist_id = ar.id
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0], "title": r[1], "price": r[2], 
                "is_sold": bool(r[3]), "artist": r[4] or "Unknown", 
                "image_url": f"http://127.0.0.1:8000/api/image/{r[5]}"
            } for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/login")
async def login(data: LoginData):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (data.username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        stored_hash = user[2].encode('utf-8')
        user_password = data.password.encode('utf-8')
        
        # Проверяем пароль напрямую через bcrypt
        if bcrypt.checkpw(user_password, stored_hash):
            return {
                "status": "success",
                "user": {"id": user[0], "username": user[1], "role": user[3]}
            }
    
    raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    raise HTTPException(status_code=401, detail="Неверный логин или пароль")
@app.get("/api/image/{image_id}")
async def get_image(image_id: str):
    image_path = os.path.join(BASE_DIR, "public", "img", f"{image_id}.jpg")
    if os.path.exists(image_path):
        return FileResponse(image_path)
    raise HTTPException(status_code=404, detail="Image not found")

# 2. Удаление картины (Только для админа)
@app.delete("/api/artworks/{art_id}")
async def delete_artwork(art_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM artworks WHERE id = ?", (art_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

# 3. Блокировка пользователя
@app.post("/api/users/block/{user_id}")
async def block_user(user_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # Просто меняем роль на 'blocked'
    cursor.execute("UPDATE users SET role = 'blocked' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"status": "user blocked"}

# УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ (Только для админа)
@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    if user_id == 1:
        raise HTTPException(status_code=400, detail="Нельзя удалить главного администратора")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return {"status": "success", "message": f"User {user_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ПОЛУЧЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ (Чтобы админ их видел)
@app.get("/api/users")
async def get_users():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    conn.close()
    return [{"id": u[0], "username": u[1], "role": u[2]} for u in users]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)