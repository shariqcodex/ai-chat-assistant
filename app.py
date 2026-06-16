from flask import Flask, request, jsonify, render_template_string
from groq import Groq
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import json

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def save_history(messages):
    with open("history.json", "w") as f:
        json.dump(messages, f, indent=2)

def load_history():
    if os.path.exists("history.json"):
        with open("history.json", "r") as f:
            return json.load(f)
    return [{"role": "system", "content": "You are a helpful assistant."}]

messages = load_history()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)

@login_manager.user_loader
def user_loader(user_id):
    users = load_users()
    if user_id in users:
        u = users[user_id]
        return User(user_id, u['username'], u['password'])
    return None

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #f3f3ef; font-family: 'Segoe UI', sans-serif; height: 100vh; display: flex; align-items: center; justify-content: center; }
        .box { background: white; border: 1px solid #e0e0d8; border-radius: 16px; padding: 40px; width: 360px; }
        h2 { margin-bottom: 24px; font-size: 20px; }
        input { width: 100%; padding: 10px 14px; border: 1px solid #e0e0d8; border-radius: 8px; font-size: 15px; margin-bottom: 12px; outline: none; }
        button { width: 100%; background: #1a1a1a; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 15px; cursor: pointer; }
        button:hover { background: #333; }
        p { margin-top: 16px; font-size: 13px; color: #888; text-align: center; }
        a { color: #1a1a1a; }
        #error { color: red; font-size: 13px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Login</h2>
        <div id="error"></div>
        <input id="username" type="text" placeholder="Username">
        <input id="password" type="password" placeholder="Password">
        <button onclick="login()">Login</button>
        <p>No account? <a href="/register">Register</a></p>
    </div>
    <script>
        async function login() {
            const res = await fetch('/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: document.getElementById('username').value,
                    password: document.getElementById('password').value
                })
            });
            const data = await res.json();
            if (data.status === 'logged in') window.location.href = '/';
            else document.getElementById('error').innerText = data.error;
        }
    </script>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Register</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #f3f3ef; font-family: 'Segoe UI', sans-serif; height: 100vh; display: flex; align-items: center; justify-content: center; }
        .box { background: white; border: 1px solid #e0e0d8; border-radius: 16px; padding: 40px; width: 360px; }
        h2 { margin-bottom: 24px; font-size: 20px; }
        input { width: 100%; padding: 10px 14px; border: 1px solid #e0e0d8; border-radius: 8px; font-size: 15px; margin-bottom: 12px; outline: none; }
        button { width: 100%; background: #1a1a1a; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 15px; cursor: pointer; }
        button:hover { background: #333; }
        p { margin-top: 16px; font-size: 13px; color: #888; text-align: center; }
        a { color: #1a1a1a; }
        #error { color: red; font-size: 13px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Create Account</h2>
        <div id="error"></div>
        <input id="username" type="text" placeholder="Username">
        <input id="password" type="password" placeholder="Password">
        <button onclick="register()">Register</button>
        <p>Have an account? <a href="/login">Login</a></p>
    </div>
    <script>
        async function register() {
            const res = await fetch('/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: document.getElementById('username').value,
                    password: document.getElementById('password').value
                })
            });
            const data = await res.json();
            if (data.status === 'registered') window.location.href = '/login';
            else document.getElementById('error').innerText = data.error;
        }
    </script>
</body>
</html>
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #f3f3ef; color: #1a1a1a; font-family: 'Segoe UI', sans-serif; height: 100vh; display: flex; flex-direction: column; }
        #header { padding: 16px 24px; background: #f3f3ef; border-bottom: 1px solid #e0e0d8; font-size: 17px; font-weight: 600; }
        #chat { flex: 1; overflow-y: auto; padding: 30px 20px; display: flex; flex-direction: column; gap: 16px; max-width: 780px; width: 100%; margin: 0 auto; }
        .message { max-width: 80%; padding: 12px 16px; border-radius: 16px; line-height: 1.6; font-size: 15px; }
        .user { background: #e8e8e2; align-self: flex-end; border-radius: 16px 16px 4px 16px; }
        .ai { background: white; align-self: flex-start; border-radius: 16px 16px 16px 4px; border: 1px solid #e0e0d8; max-width: 85%; }
        #input-wrapper { padding: 16px 20px 24px; background: #f3f3ef; }
        #input-box { max-width: 780px; margin: 0 auto; background: white; border: 1px solid #e0e0d8; border-radius: 16px; padding: 12px 16px; display: flex; gap: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        #prompt { flex: 1; background: transparent; border: none; color: #1a1a1a; font-size: 15px; outline: none; font-family: 'Segoe UI', sans-serif; }
        #prompt::placeholder { color: #aaa; }
        #send { background: #1a1a1a; color: white; border: none; width: 34px; height: 34px; border-radius: 8px; cursor: pointer; font-size: 16px; }
        #send:hover { background: #333; }
    </style>
</head>
<body>
    <div id="header">✨ AI Assistant</div>
    <div id="chat"></div>
    <div id="input-wrapper">
        <div id="input-box">
            <input id="prompt" type="text" placeholder="Write a message...">
            <button id="send" onclick="sendMessage()">↑</button>
        </div>
    </div>
    <script>
        async function sendMessage() {
            const prompt = document.getElementById('prompt');
            const text = prompt.value.trim();
            if (!text) return;
            addMessage(text, 'user');
            prompt.value = '';
            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text})
            });
            const data = await res.json();
            addMessage(data.reply, 'ai');
        }

        function addMessage(text, role) {
            const div = document.createElement('div');
            div.className = 'message ' + role;
            div.innerText = text;
            document.getElementById('chat').appendChild(div);
            document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
        }

        document.getElementById('prompt').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
"""

@app.route('/')
@login_required
def home():
    return render_template_string(HTML)

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    messages.append({"role": "user", "content": data['message']})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    save_history(messages)
    return jsonify({"reply": reply})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        users = load_users()
        if data['username'] in users:
            return jsonify({'error': 'Username already exists'})
        users[data['username']] = {
            'username': data['username'],
            'password': generate_password_hash(data['password'])
        }
        save_users(users)
        return jsonify({'status': 'registered'})
    return render_template_string(REGISTER_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        users = load_users()
        if data['username'] in users:
            user = users[data['username']]
            if check_password_hash(user['password'], data['password']):
                u = User(data['username'], data['username'], user['password'])
                login_user(u)
                return jsonify({'status': 'logged in'})
        return jsonify({'error': 'Invalid credentials'})
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'status': 'logged out'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))