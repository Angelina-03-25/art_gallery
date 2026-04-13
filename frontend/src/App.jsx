import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [artworks, setArtworks] = useState([]);
  const [showLogin, setShowLogin] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [allUsers, setAllUsers] = useState([]);
  const [newArt, setNewArt] = useState({ title: '', price: '', artist_id: 1, image: null });
  const [artists, setArtists] = useState([]);
  const [isEditing, setIsEditing] = useState(null); 
  const [editForm, setEditForm] = useState({ title: '', price: '', artist_id: '' });


  const handleAddArtist = async () => {
    const name = prompt("Введите имя нового автора:");
    if (!name) return;
    const res = await fetch('http://127.0.0.1:8000/api/artists', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    if (res.ok) fetchArtists();
  };

  const fetchArtists = async () => {
    const res = await fetch('http://127.0.0.1:8000/api/artists');
    const data = await res.json();
    setArtists(data);
  };

  useEffect(() => {
    fetchArtists();
  }, []);

  const handleAddArt = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('title', newArt.title);
    formData.append('price', newArt.price);
    formData.append('artist_id', newArt.artist_id);
    formData.append('image', newArt.image);

    const res = await fetch('http://127.0.0.1:8000/api/artworks', {
      method: 'POST',
      body: formData 
    });

    if (res.ok) {
      alert("Картина успешно добавлена!");
      fetchArtworks(); 
      setNewArt({ title: '', price: '', artist_id: 1, image: null });
    }
  };

  const fetchUsers = async () => {
    if (user?.role !== 'admin') return;
    const res = await fetch('http://127.0.0.1:8000/api/users');
    const data = await res.json();
    setAllUsers(data);
  };

  useEffect(() => {
    if (isLoggedIn && user?.role === 'admin') {
      fetchUsers();
    }
  }, [isLoggedIn, user]);

  const handleDeleteUser = async (userId) => {
    if (!window.confirm("Вы уверены, что хотите исключить этого пользователя из клуба?")) return;
    const res = await fetch(`http://127.0.0.1:8000/api/users/${userId}`, { method: 'DELETE' });
    if (res.ok) fetchUsers();
  };

  const fetchArtworks = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/artworks');
      const data = await res.json();
      setArtworks(data);
    } catch (err) {
      console.error("Ошибка загрузки:", err);
    }
  };

  useEffect(() => {
    fetchArtworks();
  }, []);

  const handleAuth = async (e) => {
    e.preventDefault();
    const endpoint = isRegister ? 'register' : 'login';
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      });
      const data = await response.json();

      if (response.ok) {
        if (isRegister) {
          alert("Регистрация успешна! Теперь войдите.");
          setIsRegister(false);
        } else {
          setUser(data.user);
          setIsLoggedIn(true);
          setShowLogin(false);
        }
      } else {
        alert(data.detail || "Ошибка доступа");
      }
    } catch (err) {
      alert("Ошибка соединения с сервером");
    }
  };

  const deleteArtwork = async (id) => {
    if (!window.confirm("Удалить этот шедевр из базы?")) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/artworks/${id}`, { method: 'DELETE' });
      if (res.ok) fetchArtworks();
    } catch (err) {
      alert("Ошибка при удалении");
    }
  };

  const startEdit = (art) => {
    setIsEditing(art.id);
    const artist = artists.find(a => a.name === art.artist);
    setEditForm({ 
      title: art.title, 
      price: art.price, 
      artist_id: artist ? artist.id : (artists[0]?.id || '') 
    });
  };

  const cancelEdit = () => {
    setIsEditing(null);
  };

  const handleUpdateArt = async (e) => {
    e.preventDefault();
    const res = await fetch(`http://127.0.0.1:8000/api/artworks/${isEditing}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editForm)
    });

    if (res.ok) {
      setIsEditing(null);
      fetchArtworks();
    }
  };

  return (
    <div className="app-container">
      <nav className="side-nav">
        <div className="logo" onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})}>AG</div>
        <div className="nav-auth" onClick={() => isLoggedIn ? (setIsLoggedIn(false), setUser(null)) : setShowLogin(true)}>
          {isLoggedIn ? 'Logout' : 'Login'}
        </div>
        <div className="nav-links">
          <a href="#catalog">Каталог</a>
          <a href="#collections">Коллекции</a>
          <a href="#authors">Авторы</a>
        </div>
      </nav>

      <main className="main-content">
        <section className="hero">
          <div className="hero-text">
            <h1 className="hero-title">Искусство вне времени<br /><span>эксклюзивно.</span></h1>
            
            <p className="hero-description">
              {isLoggedIn 
                ? `Добро пожаловать, ${user?.username}. Вам открыт полный доступ к архивам закрытого клуба.` 
                : 'Присоединяйтесь к сообществу коллекционеров, чтобы получить доступ к редким полотнам.'}
            </p>

            <div className="hero-controls">
              {!isLoggedIn ? (
                <button className="btn-primary" onClick={() => { setIsRegister(true); setShowLogin(true); }}>
                  Стать частью клуба
                </button>
              ) : (
                <button className="btn-primary" onClick={() => document.getElementById('catalog').scrollIntoView({behavior: 'smooth'})}>
                  Моя коллекция
                </button>
              )}
              
              <button className="btn-secondary" onClick={() => document.getElementById('catalog').scrollIntoView({behavior: 'smooth'})}>
                Смотреть каталог
              </button>
            </div>
          </div>
        </section>

        {user?.role === 'admin' && (
          <section className="admin-panel-users">
            <div className="container">
              <h2 className="admin-title">Управление резидентами клуба</h2>
              <div className="users-list">
                {allUsers.map(u => (
                  <div key={u.id} className="user-item">
                    <div className="user-info">
                      <span className="user-id">#{u.id}</span>
                      <span className="user-name">{u.username}</span>
                      <span className={`user-role ${u.role}`}>{u.role}</span>
                    </div>
                    {u.id !== user.id && (
                      <button className="btn-delete-user" onClick={() => handleDeleteUser(u.id)}>Исключить</button>
                    )}
                  </div>
                ))}
              </div>
            </div>
            <div className="admin-add-art">
              <h3 className="admin-sub-title">Добавить новый экспонат</h3>
              <form onSubmit={handleAddArt} className="add-art-form">
                <input type="text" placeholder="Название картины" required
                  value={newArt.title} onChange={e => setNewArt({...newArt, title: e.target.value})} />
                
                <input type="number" placeholder="Оценка (USD $)" required
                  value={newArt.price} onChange={e => setNewArt({...newArt, price: e.target.value})} />
                
                <div className="artist-select-group">
                  <select value={newArt.artist_id} onChange={e => setNewArt({...newArt, artist_id: e.target.value})}>
                    {artists.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                  </select>
                  <button type="button" onClick={handleAddArtist} className="btn-add-small">+</button>
                </div>

                <input type="file" accept="image/*" required
                  onChange={e => setNewArt({...newArt, image: e.target.files[0]})} />
                
                <button type="submit" className="btn-primary">Опубликовать</button>
              </form>
            </div>
          </section>
        )}

        <section id="catalog" className="catalog-section">
          <h2 className="section-title">Экспозиция</h2>
          <div className="art-grid">
            {artworks.map(art => (
              <div key={art.id} className={`art-card ${isEditing === art.id ? 'editing' : ''}`}>
                <div className="art-image-container">
                  <img src={art.image_url} alt={art.title} className="art-image" />
                  {art.is_sold && <div className="sold-badge">Sold</div>}
                  
                  {user?.role === 'admin' && (
                    <>
                      {isEditing === art.id ? (
                        <div className="admin-card-actions editing-mode">
                          <button className="save-btn" onClick={handleUpdateArt}>💾</button>
                          <button className="cancel-btn" onClick={cancelEdit}>✕</button>
                        </div>
                      ) : (
                        <>
                          <button className="delete-btn" onClick={() => deleteArtwork(art.id)}>✕</button>
                          <button className="edit-btn" onClick={() => startEdit(art)}>✎</button>
                        </>
                      )}
                    </>
                  )}
                </div>

                <div className="art-info">
                  {isEditing === art.id ? (
                    <div className="edit-art-inline-form">
                      <select 
                        value={editForm.artist_id} 
                        onChange={e => setEditForm({...editForm, artist_id: e.target.value})}
                        className="edit-input artist-input"
                      >
                        {artists.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                      </select>
                      <input 
                        type="text" 
                        value={editForm.title} 
                        onChange={e => setEditForm({...editForm, title: e.target.value})}
                        className="edit-input title-input"
                      />
                      <div className="price-input-wrapper">
                        <span>$</span>
                        <input 
                          type="number" 
                          value={editForm.price} 
                          onChange={e => setEditForm({...editForm, price: e.target.value})}
                          className="edit-input price-input"
                        />
                      </div>
                    </div>
                  ) : (
                    <>
                      <span className="art-artist">{art.artist}</span>
                      <h3 className="art-title">{art.title}</h3>
                      <p className="art-price">${art.price.toLocaleString('en-US')}</p>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      {showLogin && (
        <div className="modal-overlay" onClick={() => setShowLogin(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setShowLogin(false)}>✕</button>
            <h2 className="modal-title">{isRegister ? 'Регистрация' : 'Вход в Клуб'}</h2>
            <form onSubmit={handleAuth}>
              <input className="modal-input" type="text" placeholder="Логин" required
                onChange={e => setLoginForm({...loginForm, username: e.target.value})} />
              <input className="modal-input" type="password" placeholder="Пароль" required
                onChange={e => setLoginForm({...loginForm, password: e.target.value})} />
              <button type="submit" className="btn-primary w-full">
                {isRegister ? 'Создать аккаунт' : 'Войти'}
              </button>
            </form>
            <p className="auth-toggle-text" onClick={() => setIsRegister(!isRegister)}>
              {isRegister ? 'Уже есть аккаунт? Войти' : 'Нет аккаунта? Стать частью клуба'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;