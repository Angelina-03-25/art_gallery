from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Получаем путь к текущей папке проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Путь к картинкам внутри public/img
IMAGES_DIR = os.path.join(BASE_DIR, "public", "img")

# 1. Запрос на получение картинки (то, что просил преподаватель — через бэкенд)
@app.get("/api/image/{art_id}")
async def get_image(art_id: int):
    # Формируем путь к файлу, например: public/img/1.jpg
    file_path = os.path.join(IMAGES_DIR, f"{art_id}.jpg")
    
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "Картина не найдена на сервере"}

# 2. Подключаем фронтенд (папку public)
# Все файлы из public будут доступны просто по адресу http://127.0.0.1:8000
app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)