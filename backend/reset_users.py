import sqlite3
import os

# Указываем путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "gallery.db")

# Реалистичные оценки в USD (от 300к до 4.5 млн $)
market_prices = {
    1: 1200000, 2: 850000, 3: 2500000, 4: 450000, 5: 4500000,
    6: 1800000, 7: 950000, 8: 3200000, 9: 600000, 10: 1400000,
    11: 2800000, 12: 750000, 13: 1100000, 14: 2100000, 15: 550000,
    16: 1350000, 17: 3000000, 18: 900000, 19: 3800000
}

def update_catalog():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    for art_id, price in market_prices.items():
        cursor.execute("UPDATE artworks SET price = ? WHERE id = ?", (price, art_id))
    
    conn.commit()
    conn.close()
    print("✅ Цены успешно обновлены. Валюта: USD.")

if __name__ == "__main__":
    update_catalog()