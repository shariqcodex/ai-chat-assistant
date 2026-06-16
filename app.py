from flask import Flask, request, jsonify, render_template_string
from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def save_history(messages):
    with open("history.json","w") as f:
        json.dump(messages,f)


def load_history():
    if os.path.exists("history.json"):
        with open("history.json", "r") as f:
            return json.load(f)
    return [{"role": "system", "content": "You are a helpful assistant."}]


messages = load_history()




app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string(HTML)


@app.route('/chat',methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))