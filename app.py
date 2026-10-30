from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_NAME = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT NOT NULL,
            name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/accounts', methods=['GET', 'POST'])
def handle_accounts():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        name = data.get('name', '').strip()
        if not name:
            return jsonify({"error": "Name cannot be empty"}), 400
        try:
            cursor.execute("INSERT INTO accounts (name) VALUES (?)", (name,))
            # ใส่หมวดหมู่เริ่มต้นให้บัญชีใหม่
            default_cats = ["อาหาร & เครื่องดื่ม", "เดินทาง", "ช้อปปิ้ง", "เงินเดือน", "ค่าเช่าบ้าน", "อื่นๆ"]
            for cat in default_cats:
                cursor.execute("INSERT INTO categories (account, name) VALUES (?, ?)", (name, cat))
            conn.commit()
            conn.close()
            return jsonify({"status": "success"})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": "Account already exists"}), 400

    cursor.execute("SELECT name FROM accounts")
    accs = [row['name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify({"accounts": accs})

@app.route('/api/data', methods=['GET'])
def get_data():
    account = request.args.get('account', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM transactions WHERE account = ? ORDER BY id DESC", (account,))
    txs = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT name FROM categories WHERE account = ?", (account,))
    cats = [row['name'] for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({"transactions": txs, "categories": cats})

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (account, type, title, amount, category, date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['account'], data['type'], data['title'], data['amount'], data['category'], data['date']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/transactions/<int:tx_id>', methods=['PUT'])
def update_transaction(tx_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE transactions 
        SET type = ?, category = ?, date = ?, title = ?, amount = ?
        WHERE id = ?
    ''', (data['type'], data['category'], data['date'], data['title'], data['amount'], tx_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/transactions/<int:tx_id>', methods=['DELETE'])
def delete_transaction(tx_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.json
    account = data.get('account')
    cat_name = data.get('name', '').strip()
    if not cat_name or not account:
        return jsonify({"error": "Invalid data"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (account, name) VALUES (?, ?)", (account, cat_name))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Category already exists"}), 400

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

