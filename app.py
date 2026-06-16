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
        try:
            with open("history.json", "r") as f:
                return json.load(f)
        except:
            pass
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
        body { background: #0d0d0f; color: #e8e8e8; font-family: 'Segoe UI', sans-serif; height: 100vh; display: flex; align-items: center; justify-content: center; }
        .box { background: #111114; border: 1px solid #222; border-radius: 16px; padding: 40px; width: 360px; }
        h2 { margin-bottom: 24px; font-size: 20px; color: white; }
        input { width: 100%; padding: 10px 14px; background: #0d0d0f; border: 1px solid #222; border-radius: 8px; font-size: 15px; margin-bottom: 12px; outline: none; color: #e8e8e8; }
        input::placeholder { color: #444; }
        button { width: 100%; background: #5b5bf7; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 15px; cursor: pointer; }
        button:hover { background: #4a4ae0; }
        p { margin-top: 16px; font-size: 13px; color: #555; text-align: center; }
        a { color: #5b5bf7; text-decoration: none; }
        #error { color: #ff6b6b; font-size: 13px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>✦ Chatron AI</h2>
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
        document.addEventListener('keydown', e => { if (e.key === 'Enter') login(); });
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
        body { background: #0d0d0f; color: #e8e8e8; font-family: 'Segoe UI', sans-serif; height: 100vh; display: flex; align-items: center; justify-content: center; }
        .box { background: #111114; border: 1px solid #222; border-radius: 16px; padding: 40px; width: 360px; }
        h2 { margin-bottom: 24px; font-size: 20px; color: white; }
        input { width: 100%; padding: 10px 14px; background: #0d0d0f; border: 1px solid #222; border-radius: 8px; font-size: 15px; margin-bottom: 12px; outline: none; color: #e8e8e8; }
        input::placeholder { color: #444; }
        button { width: 100%; background: #5b5bf7; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 15px; cursor: pointer; }
        button:hover { background: #4a4ae0; }
        p { margin-top: 16px; font-size: 13px; color: #555; text-align: center; }
        a { color: #5b5bf7; text-decoration: none; }
        #error { color: #ff6b6b; font-size: 13px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>✦ Create Account</h2>
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
        document.addEventListener('keydown', e => { if (e.key === 'Enter') register(); });
    </script>
</body>
</html>
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Chatron AI</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0d0d0f; color: #e8e8e8; font-family: 'Segoe UI', sans-serif; height: 100vh; display: flex; }

        #sidebar { width: 260px; background: #111114; border-right: 1px solid #1e1e24; display: flex; flex-direction: column; padding: 20px 16px; gap: 8px; }
        #sidebar-title { font-size: 18px; font-weight: 700; color: white; padding: 8px 12px; margin-bottom: 8px; }
        .sidebar-btn { background: none; border: none; color: #666; padding: 10px 12px; border-radius: 8px; cursor: pointer; font-size: 14px; text-align: left; width: 100%; transition: all 0.2s; display: flex; align-items: center; gap: 8px; }
        .sidebar-btn:hover { background: #1e1e24; color: white; }
        .sidebar-btn.active { background: #1e1e24; color: white; }
        #sidebar-bottom { margin-top: auto; display: flex; flex-direction: column; gap: 8px; border-top: 1px solid #1e1e24; padding-top: 16px; }
        .user-info { padding: 10px 12px; font-size: 13px; color: #444; }

        #main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        #header { padding: 20px 32px; border-bottom: 1px solid #1a1a1f; font-size: 15px; color: #444; }

        #chat { flex: 1; overflow-y: auto; padding: 32px; display: flex; flex-direction: column; gap: 24px; max-width: 860px; width: 100%; margin: 0 auto; }
        #chat::-webkit-scrollbar { width: 6px; }
        #chat::-webkit-scrollbar-track { background: transparent; }
        #chat::-webkit-scrollbar-thumb { background: #1e1e24; border-radius: 3px; }
        #chat::-webkit-scrollbar-thumb:hover { background: #2a2a35; }

        #welcome { text-align: center; padding: 60px 0; }
        #welcome h1 { font-size: 28px; font-weight: 600; margin-bottom: 8px; }
        #welcome p { color: #444; font-size: 15px; }

        .message { max-width: 75%; padding: 14px 18px; border-radius: 16px; font-size: 15px; line-height: 1.7; }
        .user { background: #1a1a2e; color: #e8e8e8; align-self: flex-end; border-radius: 16px 16px 4px 16px; border: 1px solid #2a2a40; }
        .ai { background: #111114; color: #e8e8e8; align-self: flex-start; border-radius: 16px 16px 16px 4px; border: 1px solid #1e1e24; max-width: 85%; }
        .ai p { margin-bottom: 8px; }
        .ai p:last-child { margin-bottom: 0; }
        .ai code { background: #1a1a2e; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; }
        .ai pre { background: #1a1a2e; padding: 12px; border-radius: 8px; overflow-x: auto; margin: 8px 0; }
        .ai ul, .ai ol { padding-left: 20px; margin: 8px 0; }
        .ai li { margin: 4px 0; }
        .ai strong { color: white; }

        .thinking-msg { background: #111114; border: 1px solid #1e1e24; padding: 16px 20px; display: flex; gap: 6px; align-items: center; border-radius: 16px 16px 16px 4px; align-self: flex-start; }
        .dot { width: 7px; height: 7px; background: #5b5bf7; border-radius: 50%; animation: bounce 1.2s infinite; }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }

        #input-wrapper { padding: 20px 32px 28px; max-width: 860px; width: 100%; margin: 0 auto; align-self: center; box-sizing: border-box; }
        #input-box { background: #111114; border: 1px solid #1e1e24; border-radius: 14px; padding: 14px 18px; display: flex; gap: 12px; align-items: center; }
        #prompt { flex: 1; background: transparent; border: none; color: #e8e8e8; font-size: 15px; outline: none; font-family: 'Segoe UI', sans-serif; }
        #prompt::placeholder { color: #333; }
        #send { background: #5b5bf7; color: white; border: none; width: 36px; height: 36px; border-radius: 8px; cursor: pointer; font-size: 16px; transition: all 0.2s; }
        #send:hover { background: #4a4ae0; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div id="sidebar-title">✦ Chatron AI</div>
        <button class="sidebar-btn active">💬 New Chat</button>
        <div id="sidebar-bottom">
            <div class="user-info">Logged in</div>
            <button class="sidebar-btn" onclick="logout()">⬡ Logout</button>
            <button class="sidebar-btn" onclick="window.location.href='/register'">＋ New Account</button>
        </div>
    </div>

    <div id="main">
        <div id="header">Ask anything</div>
        <div id="chat">
            <div id="welcome">
                <h1>Good Evening 👋</h1>
                <p>How can I help you today?</p>
            </div>
        </div>
        <div id="input-wrapper">
            <div id="input-box">
                <input id="prompt" type="text" placeholder="Ask anything...">
                <button id="send" onclick="sendMessage()">↑</button>
            </div>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const prompt = document.getElementById('prompt');
            const text = prompt.value.trim();
            if (!text) return;

            document.getElementById('welcome').style.display = 'none';
            addMessage(text, 'user');
            prompt.value = '';

            const thinking = document.createElement('div');
            thinking.className = 'thinking-msg';
            thinking.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
            document.getElementById('chat').appendChild(thinking);
            thinking.scrollIntoView();

            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text})
            });
            const data = await res.json();
            thinking.remove();

            const aiDiv = addMessage('', 'ai');
            aiDiv.innerHTML = marked.parse(data.reply);
            aiDiv.scrollIntoView();
        }

        function addMessage(text, role) {
            const div = document.createElement('div');
            div.className = 'message ' + role;
            if (text) div.innerText = text;
            document.getElementById('chat').appendChild(div);
            div.scrollIntoView();
            return div;
        }

        async function logout() {
            await fetch('/logout');
            window.location.href = '/login';
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