from flask import Flask, request, jsonify, render_template_string
from groq import Groq
from dotenv import load_dotenv
import markdown
import os
import json

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return [
        {
            "role": "system",
            "content": "You are a helpful assistant. Be concise, smart and straight to the point. Use emojis naturally in your responses."
        }
    ]

def save_history(messages):
    with open(HISTORY_FILE, "w") as f:
        json.dump(messages, f, indent=2)

messages = load_history()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #f3f3ef; color: #1a1a1a; font-family: 'Segoe UI', sans-serif; height: 100vh; display: flex; flex-direction: column; }
        
        #header { 
            padding: 16px 24px; 
            background: #f3f3ef;
            border-bottom: 1px solid #e0e0d8; 
            font-size: 17px; 
            font-weight: 600; 
            color: #1a1a1a;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        #header-left { display: flex; align-items: center; gap: 10px; }
        #header span { font-size: 22px; }
        #clear-btn {
            background: none;
            border: 1px solid #e0e0d8;
            color: #888;
            padding: 6px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
        }
        #clear-btn:hover { background: #e8e8e2; color: #1a1a1a; }

        #chat { 
            flex: 1; 
            overflow-y: auto; 
            padding: 30px 20px; 
            display: flex; 
            flex-direction: column; 
            gap: 16px;
            max-width: 780px;
            width: 100%;
            margin: 0 auto;
        }

        .message { 
            max-width: 80%; 
            padding: 12px 16px; 
            border-radius: 16px; 
            line-height: 1.6; 
            font-size: 15px;
        }
        .user { 
            background: #e8e8e2; 
            color: #1a1a1a; 
            align-self: flex-end; 
            border-radius: 16px 16px 4px 16px; 
        }
        .ai { 
            background: white; 
            color: #1a1a1a; 
            align-self: flex-start; 
            border-radius: 16px 16px 16px 4px; 
            border: 1px solid #e0e0d8;
            max-width: 85%;
        }
        .ai p { margin-bottom: 8px; }
        .ai p:last-child { margin-bottom: 0; }
        .ai strong { color: #1a1a1a; font-weight: 600; }
        .ai ul, .ai ol { padding-left: 20px; margin: 8px 0; }
        .ai li { margin: 4px 0; }
        .ai code { background: #f0f0ea; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; }
        .ai pre { background: #f0f0ea; padding: 12px; border-radius: 8px; overflow-x: auto; margin: 8px 0; }
        .ai pre code { background: none; padding: 0; }
        .thinking { color: #999; font-style: italic; background: white; border: 1px solid #e0e0d8; }

        #input-wrapper {
            padding: 16px 20px 24px;
            background: #f3f3ef;
        }
        #input-box {
            max-width: 780px;
            margin: 0 auto;
            background: white;
            border: 1px solid #e0e0d8;
            border-radius: 16px;
            padding: 12px 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        #prompt { 
            width: 100%;
            background: transparent; 
            border: none;
            color: #1a1a1a; 
            font-size: 15px; 
            outline: none; 
            resize: none;
            font-family: 'Segoe UI', sans-serif;
            line-height: 1.5;
            max-height: 120px;
            overflow-y: auto;
        }
        #prompt::placeholder { color: #aaa; }
        #input-actions { display: flex; align-items: center; justify-content: space-between; }
        #left-actions { display: flex; gap: 6px; }
        .action-btn {
            background: none;
            border: 1px solid #e0e0d8;
            color: #666;
            width: 34px;
            height: 34px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .action-btn:hover { background: #f0f0ea; color: #1a1a1a; }
        #right-actions { display: flex; gap: 6px; align-items: center; }
        #send { 
            background: #1a1a1a;
            color: white; 
            border: none; 
            width: 34px;
            height: 34px;
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        #send:hover { background: #333; }
        #send:disabled { background: #ccc; cursor: not-allowed; }
        #file-input { display: none; }
        .file-preview {
            background: #f0f0ea;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 13px;
            color: #555;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .file-preview button { background: none; border: none; color: #999; cursor: pointer; font-size: 16px; }
        #model-info { font-size: 12px; color: #aaa; text-align: center; margin-top: 8px; }
    </style>
</head>
<body>
    <div id="header">
        <div id="header-left"><span>✨</span> AI Assistant</div>
        <button id="clear-btn" onclick="clearHistory()">🗑 Clear History</button>
    </div>
    <div id="chat"></div>
    <div id="input-wrapper">
        <div id="input-box">
            <div id="file-preview-area"></div>
            <textarea id="prompt" placeholder="Write a message..." rows="1"></textarea>
            <div id="input-actions">
                <div id="left-actions">
                    <button class="action-btn" onclick="document.getElementById('file-input').click()" title="Attach file">＋</button>
                    <input type="file" id="file-input" accept=".txt,.pdf,.py,.js,.csv" onchange="handleFile(event)">
                </div>
                <div id="right-actions">
                    <button class="action-btn" id="voice-btn" title="Voice input">🎤</button>
                    <button id="send" title="Send">↑</button>
                </div>
            </div>
        </div>
        <div id="model-info">Llama 3.3 · 70B</div>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const prompt = document.getElementById('prompt');
        const send = document.getElementById('send');
        let attachedText = '';

        // Load existing history on page load
        window.onload = async () => {
            const res = await fetch('/history');
            const data = await res.json();
            data.forEach(msg => {
                if (msg.role === 'user') addMessage(msg.content, 'user');
                if (msg.role === 'assistant') addMessage(msg.content, 'ai', true);
            });
        };

        async function clearHistory() {
            await fetch('/clear', { method: 'POST' });
            chat.innerHTML = '';
        }

        prompt.addEventListener('input', () => {
            prompt.style.height = 'auto';
            prompt.style.height = prompt.scrollHeight + 'px';
        });

        function addMessage(text, role, isHTML = false) {
            const div = document.createElement('div');
            div.className = `message ${role}`;
            if (isHTML) { div.innerHTML = text; } else { div.innerText = text; }
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
            return div;
        }

        function handleFile(event) {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (e) => {
                attachedText = e.target.result;
                document.getElementById('file-preview-area').innerHTML = `
                    <div class="file-preview">📎 ${file.name}<button onclick="clearFile()">✕</button></div>`;
            };
            reader.readAsText(file);
        }

        function clearFile() {
            attachedText = '';
            document.getElementById('file-preview-area').innerHTML = '';
            document.getElementById('file-input').value = '';
        }

        const voiceBtn = document.getElementById('voice-btn');
        let recognition;
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SR();
            recognition.lang = 'en-US';
            recognition.onresult = (e) => {
                prompt.value += e.results[0][0].transcript;
                prompt.style.height = 'auto';
                prompt.style.height = prompt.scrollHeight + 'px';
            };
            recognition.onend = () => { voiceBtn.style.color = ''; };
        }

        voiceBtn.addEventListener('click', () => {
            if (recognition) { voiceBtn.style.color = 'red'; recognition.start(); }
        });

        async function sendMessage() {
            let text = prompt.value.trim();
            if (!text && !attachedText) return;
            if (attachedText) text = text + '\\n\\n[Attached file]:\\n' + attachedText;

            const displayText = prompt.value.trim() || 'File attached';
            prompt.value = '';
            prompt.style.height = 'auto';
            clearFile();
            send.disabled = true;

            addMessage(displayText, 'user');
            const thinking = addMessage('Thinking...', 'ai thinking');

            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await res.json();
            thinking.remove();
            addMessage(data.reply, 'ai', true);
            send.disabled = false;
        }

        send.addEventListener('click', sendMessage);
        prompt.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/history')
def get_history():
    history = [m for m in messages if m['role'] != 'system']
    formatted = []
    for m in history:
        if m['role'] == 'assistant':
            formatted.append({"role": "assistant", "content": markdown.markdown(m['content'], extensions=['fenced_code'])})
        else:
            formatted.append(m)
    return jsonify(formatted)

@app.route('/clear', methods=['POST'])
def clear():
    global messages
    messages = [{"role": "system", "content": "You are a helpful assistant. Be concise, smart and straight to the point. Use emojis naturally in your responses."}]
    save_history(messages)
    return jsonify({"status": "cleared"})

@app.route('/chat', methods=['POST'])
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

    formatted = markdown.markdown(reply, extensions=['fenced_code'])
    return jsonify({"reply": formatted})

if __name__ == '__main__':
    app.run(debug=True)