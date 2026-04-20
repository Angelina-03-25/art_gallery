import sqlite3

# Connect to the database
connection = sqlite3.connect('art_gallery.db')

# Create a cursor object
cursor = connection.cursor()

# Create tables
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS artists (
    artist_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    bio TEXT,
    date_of_birth TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS collections (
    collection_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS artworks (
    artwork_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    artist_id INTEGER,
    FOREIGN KEY (artist_id) REFERENCES artists (artist_id)
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS artwork_collections (
    artwork_collection_id INTEGER PRIMARY KEY,
    artwork_id INTEGER,
    collection_id INTEGER,
    FOREIGN KEY (artwork_id) REFERENCES artworks (artwork_id),
    FOREIGN KEY (collection_id) REFERENCES collections (collection_id)
)''')

# Insert test data
cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'adminpass', 'admin')")
cursor.execute("INSERT INTO artists (name, bio, date_of_birth) VALUES ('Vincent van Gogh', 'Dutch Post-Impressionist painter.', '1853-03-30')")
cursor.execute("INSERT INTO artworks (title, artist_id) VALUES ('Starry Night', 1)")

# Commit the changes and close the connection
connection.commit()
connection.close()