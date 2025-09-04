from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import argparse
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

app = Flask(__name__)
app.secret_key = 'phantom_secret_key_123'

# Initialize database
def init_db():
    conn = sqlite3.connect('accs.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  wallet_data TEXT DEFAULT '{}')''')
    conn.commit()
    conn.close()

# Check if user exists and password is correct
def check_user(username, password):
    conn = sqlite3.connect('accs.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and check_password_hash(result[0], password):
        return True
    return False

# Get user wallet data
def get_user_wallet_data(username):
    conn = sqlite3.connect('accs.db')
    c = conn.cursor()
    c.execute("SELECT wallet_data FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0]:
        return json.loads(result[0])
    return {
        'balance': 0,
        'solBalance': 0,
        'solPrice': 200,
        'refreshCount': 0,
        'refreshGoal': 3,
        'newBalance': 1000,
        'previousBalance': 0
    }

# Save user wallet data
def save_user_wallet_data(username, wallet_data):
    conn = sqlite3.connect('accs.db')
    c = conn.cursor()
    c.execute("UPDATE users SET wallet_data = ? WHERE username = ?", 
             (json.dumps(wallet_data), username))
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    if 'username' in session:
        wallet_data = get_user_wallet_data(session['username'])
        return render_template('index.html', 
                             username=session['username'],
                             wallet_data=wallet_data)
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if check_user(username, password):
            session['username'] = username
            return redirect('/')
        else:
            return render_template('login.html', error='Невірний логін або пароль')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/api/wallet-data')
def api_wallet_data():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    wallet_data = get_user_wallet_data(session['username'])
    return jsonify(wallet_data)

@app.route('/api/save-wallet-data', methods=['POST'])
def api_save_wallet_data():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        save_user_wallet_data(session['username'], data)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return app.send_static_file(filename)

# CLI functions
def list_users():
    """List all users"""
    conn = sqlite3.connect('accs.db')
    c = conn.cursor()
    c.execute("SELECT id, username FROM users")
    users = c.fetchall()
    conn.close()
    
    if users:
        print("Користувачі в базі:")
        for user in users:
            print(f"ID: {user[0]}, Username: {user[1]}")
    else:
        print("В базі немає користувачів")

def create_user(username, password):
    """Create new user"""
    hashed_password = generate_password_hash(password)
    
    try:
        conn = sqlite3.connect('accs.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                 (username, hashed_password))
        conn.commit()
        conn.close()
        print(f"Користувач '{username}' успішно створений!")
    except sqlite3.IntegrityError:
        print(f"Помилка: Користувач '{username}' вже існує!")

def delete_user(username):
    """Delete user"""
    conn = sqlite3.connect('accs.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    deleted = conn.total_changes
    conn.close()
    
    if deleted > 0:
        print(f"Користувач '{username}' видалений!")
    else:
        print(f"Помилка: Користувач '{username}' не знайдений!")

if __name__ == '__main__':
    init_db()
    
    parser = argparse.ArgumentParser(description='Phantom Wallet Server')
    parser.add_argument('--port', type=int, default=5000, help='Порт сервера')
    
    subparsers = parser.add_subparsers(dest='command', help='Команди')
    
    list_parser = subparsers.add_parser('list', help='Показати всіх користувачів')
    
    create_parser = subparsers.add_parser('create', help='Створити користувача')
    create_parser.add_argument('username', help='Ім\'я користувача')
    create_parser.add_argument('password', help='Пароль')
    
    delete_parser = subparsers.add_parser('delete', help='Видалити користувача')
    delete_parser.add_argument('username', help='Ім\'я користувача')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_users()
    elif args.command == 'create':
        create_user(args.username, args.password)
    elif args.command == 'delete':
        delete_user(args.username)
    else:
        print(f"Запуск сервера на порту {args.port}...")
        print("Доступні команди:")
        print("  python server.py list - Показати користувачів")
        print("  python server.py create <username> <password> - Створити користувача")
        print("  python server.py delete <username> - Видалити користувача")
        print("\nДоступ до веб-інтерфейсу: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=args.port)