from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def save_history(messages):
    with open("history.json","w") as f:
        json.dump(messages, f, indent=2)


def load_history():
    if os.path.exists("history.json"):
        with open("history.json", "r") as f:
            return json.load(f)
    return [{"role": "system", "content": "You are a helpful assistant."}]



messages = load_history()

print("Chatbot ready. Type 'quit' to exit")

while True:
    user_input = input("You: ")

    if user_input.lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )

    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    save_history(messages)
    print(f"AI: {reply}\n")
