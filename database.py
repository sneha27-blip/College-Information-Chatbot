import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DB_NAME = "college_chatbot.db"

def get_db_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)

def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            department TEXT DEFAULT 'General',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Chat History table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def register_user(username, email, password, full_name, department="General"):
    username = username.strip().lower()
    email = email.strip().lower()
    full_name = full_name.strip()
    
    if not username or not email or not password or not full_name:
        return False, "All fields are required."
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username or email already exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return False, "Username or email is already registered."
        
        # Hash password securely using PBKDF2 / Scrypt
        hashed_pw = generate_password_hash(password)
        
        cursor.execute('''
            INSERT INTO users (username, email, full_name, password_hash, department)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, full_name, hashed_pw, department))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return True, {"id": user_id, "username": username, "full_name": full_name, "email": email}
    except Exception as e:
        conn.close()
        return False, f"Registration error: {str(e)}"

def authenticate_user(login_identifier, password):
    login_identifier = login_identifier.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Allow login by username OR email
        cursor.execute('''
            SELECT id, username, email, full_name, password_hash, department
            FROM users
            WHERE username = ? OR email = ?
        ''', (login_identifier, login_identifier))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False, "Invalid username/email or password."
        
        if check_password_hash(user["password_hash"], password):
            return True, {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "department": user["department"]
            }
        else:
            return False, "Invalid username/email or password."
    except Exception as e:
        if conn:
            conn.close()
        return False, f"Authentication error: {str(e)}"

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, full_name, department FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def save_chat_message(user_id, sender, message):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO chat_history (user_id, sender, message, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, sender, message, now_str))
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return msg_id, now_str

def get_chat_history(user_id, limit=100):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, sender, message, timestamp
        FROM chat_history
        WHERE user_id = ?
        ORDER BY id ASC
        LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_chat_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
