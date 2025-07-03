import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
DATABASE = 'document_tracker.db'
ALLOWED_EXTENSIONS = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------- DB INITIALIZATION -----------
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        # Create documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                status TEXT DEFAULT 'Submitted',
                coordinator_feedback TEXT,
                principal_feedback TEXT,
                version INTEGER DEFAULT 1,
                stage TEXT DEFAULT 'Coordinator',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Insert default users if not already present
        users = [
            ('Teacher One', 'teacher@test.com', 'test123', 'teacher'),
            ('Coordinator One', 'coordinator@test.com', 'coord123', 'coordinator'),
            ('Principal One', 'principal@test.com', 'princ123', 'principal')
        ]
        for name, email, password, role in users:
            try:
                cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                               (name, email, password, role))
            except sqlite3.IntegrityError:
                # User already exists
                pass
        conn.commit()

init_db()

# ----------- UTILS -----------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------- ROUTES -----------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                               (name, email, password, role))
                conn.commit()
                return redirect('/login')
            except sqlite3.IntegrityError:
                return "Email already exists."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                session['role'] = user[4]
                session['name'] = user[1]
                if user[4] == 'teacher':
                    return redirect('/teacher_dashboard')
                elif user[4] == 'coordinator':
                    return redirect('/coordinator_dashboard')
                elif user[4] == 'principal':
                    return redirect('/principal_dashboard')
                else:
                    return redirect('/admin_panel')
            else:
                return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/teacher_dashboard', methods=['GET', 'POST'])
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')

    user_id = session['user_id']

    if request.method == 'POST':
        title = request.form['title']
        file = request.files['document']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO documents (user_id, title, filename) VALUES (?, ?, ?)",
                               (user_id, title, filename))
                conn.commit()

    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE user_id = ?", (user_id,))
        documents = cursor.fetchall()

    return render_template('teacher_dashboard.html', user_name=session['name'], user_role=session['role'], documents=documents)

@app.route('/coordinator_dashboard')
def coordinator_dashboard():
    if 'user_id' not in session or session['role'] != 'coordinator':
        return redirect('/login')
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, u.name as teacher_name
        FROM documents d
        JOIN users u ON d.user_id = u.id
        WHERE d.stage = 'Coordinator'
    ''')
    documents = cursor.fetchall()
    conn.close()
    return render_template('coordinator_dashboard.html', documents=documents)

@app.route('/coordinator_action/<int:doc_id>', methods=['POST'])
def coordinator_action(doc_id):
    if 'user_id' not in session or session['role'] != 'coordinator':
        return redirect('/login')

    new_status = request.form['status']
    feedback = request.form['feedback']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    stage = 'Principal' if new_status == 'Approved' else 'Teacher'
    cursor.execute('''
        UPDATE documents
        SET status = ?, coordinator_feedback = ?, stage = ?
        WHERE id = ?
    ''', (new_status, feedback, stage, doc_id))
    conn.commit()
    conn.close()
    return redirect('/coordinator_dashboard')

@app.route('/principal_dashboard')
def principal_dashboard():
    if 'user_id' not in session or session['role'] != 'principal':
        return redirect('/login')
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, u.name as teacher_name
        FROM documents d
        JOIN users u ON d.user_id = u.id
        WHERE d.stage = 'Principal'
    ''')
    documents = cursor.fetchall()
    conn.close()
    return render_template('principal_dashboard.html', documents=documents)

@app.route('/principal_action/<int:doc_id>', methods=['POST'])
def principal_action(doc_id):
    if 'user_id' not in session or session['role'] != 'principal':
        return redirect('/login')

    new_status = request.form['status']
    feedback = request.form['feedback']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    stage = 'Completed' if new_status == 'Approved' else 'Teacher'
    cursor.execute('''
        UPDATE documents
        SET status = ?, principal_feedback = ?, stage = ?
        WHERE id = ?
    ''', (new_status, feedback, stage, doc_id))
    conn.commit()
    conn.close()
    return redirect('/principal_dashboard')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ---------- Add admin routes later ----------

if __name__ == '__main__':
    app.run(debug=True)
