from flask import Flask, request, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Setting up the login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Dummy user store (in real apps, use a database)
users = {}

# User class
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

# Face detection setup
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def detect_faces(image_array):
    gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return faces

# Route: Sign-up (register)
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username in users:
        return jsonify({"error": "Username already exists"}), 400

    users[username] = generate_password_hash(password)
    return jsonify({"message": f"User {username} registered successfully!"})

# Route: Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username in users and check_password_hash(users[username], password):
        user = User(username)
        login_user(user)
        return jsonify({"message": f"Logged in as {username}!"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Route: Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out!"})

# Route: Face detection (requires login)
@app.route('/detect_face', methods=['POST'])
@login_required
def detect_face():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    img_np = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

    faces = detect_faces(img)
    return jsonify({
        "faces_detected": len(faces),
        "user": current_user.id
    })

# Route: Extremist language detection (requires login)
@app.route('/detect_text', methods=['POST'])
@login_required
def detect_text():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Text not provided"}), 400

    text = data['text'].lower()
    extremist_keywords = ["bomb", "attack", "kill", "jihad", "terror"]
    found = [word for word in extremist_keywords if word in text]

    if found:
        return jsonify({"status": "warning", "keywords": found})
    else:
        return jsonify({"status": "safe"})

if __name__ == '__main__':
    app.run(debug=True)
