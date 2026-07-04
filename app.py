from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO
from flask_cors import CORS
import os
import re
import threading
import webbrowser
from datetime import datetime
from functools import wraps

# ==========================================
# CONFIG
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.config["SECRET_KEY"] = "admin_secret_key_2026_change_this"

CORS(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)

# ==========================================
# LOGIN REQUIRED DECORATOR
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# ROUTES - PUBLIC
# ==========================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/visualisasi")
def visualisasi():
    return render_template("visualisasi.html")

@app.route("/analisis")
def analisis():
    return render_template("analisis.html")

@app.route("/scraping")
def scraping():
    return render_template("scraping.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ==========================================
# ADMIN LOGIN
# ==========================================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Ganti dengan username dan password yang Anda inginkan
        if username == "admin" and password == "admin123":
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template("admin_login.html", error="Username atau password salah!")
    
    return render_template("admin_login.html")

@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# ==========================================
# ADMIN DASHBOARD
# ==========================================
@app.route("/admin")
@login_required
def admin_dashboard():
    return render_template("admin.html")

# ==========================================
# ADMIN EDITOR - EDIT SEMUA HALAMAN
# ==========================================
@app.route("/admin-editor")
@login_required
def admin_editor():
    return render_template("admin_editor.html")

# ==========================================
# API UNTUK MENYIMPAN DATA (opsional - untuk backend save)
# ==========================================
@app.route("/api/save-content", methods=["POST"])
@login_required
def save_content():
    """Menyimpan konten ke file JSON (opsional, untuk penyimpanan permanen)"""
    data = request.get_json()
    page = data.get('page')
    content = data.get('content')
    
    if not page or not content:
        return jsonify({"status": "error", "message": "Data tidak lengkap"}), 400
    
    # Simpan ke file JSON
    import json
    filename = f"data_content_{page}.json"
    filepath = os.path.join(BASE_DIR, "data", filename)
    
    # Buat folder data jika belum ada
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    
    return jsonify({"status": "success", "message": f"Konten {page} berhasil disimpan"})

# ==========================================
# PREPROCESSING & API PREDICT
# ==========================================
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def sentiment_classification(text):
    positive_words = ["bagus", "mantap", "hebat", "keren", "baik", "suka", "puas", "senang"]
    negative_words = ["buruk", "jelek", "parah", "benci", "kecewa", "sedih"]
    
    score = 0
    for word in positive_words:
        if word in text:
            score += 1
    for word in negative_words:
        if word in text:
            score -= 1
    
    if score > 0:
        return "positif", 0.90
    elif score < 0:
        return "negatif", 0.88
    return "netral", 0.70

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json()
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"status": "error", "message": "Input kosong"}), 400
    
    clean_text = preprocess_text(text)
    label, confidence = sentiment_classification(clean_text)
    
    return jsonify({
        "status": "success",
        "original_text": text,
        "clean_text": clean_text,
        "label": label,
        "confidence": round(confidence, 4),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# ==========================================
# SOCKET.IO
# ==========================================
@socketio.on("connect")
def handle_connect():
    print("Client Connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client Disconnected")

# ==========================================
# ERROR PAGE
# ==========================================
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

# ==========================================
# AUTO OPEN BROWSER
# ==========================================
def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

# ==========================================
# RUN
# ==========================================
if __name__ == "__main__":
    print("=" * 50)
    print("FinSense SVM Running")
    print("http://127.0.0.1:5000")
    print("Admin Login: http://127.0.0.1:5000/admin-login")
    print("Username: admin | Password: admin123")
    print("=" * 50)
    
    threading.Timer(1.5, open_browser).start()
    
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )