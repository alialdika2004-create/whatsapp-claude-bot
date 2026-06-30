from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Anthropic client
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# In-memory conversation history per WhatsApp number
conversations = {}

SYSTEM_PROMPT = (
    "You are a helpful assistant responding to WhatsApp messages. "
    "Keep responses concise and readable on a phone screen. "
    "You can help with any task: answering questions, writing, research, calculations, and more."
)

MAX_HISTORY = 20  # messages to keep per user


@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")

    if not body:
        return _reply("(empty message received)")

    # Reset conversation on command
    if body.lower() in ("/reset", "reset", "/clear", "clear"):
        conversations.pop(from_number, None)
        return _reply("Conversation cleared. Starting fresh!")

    # Build history
    history = conversations.setdefault(from_number, [])
    history.append({"role": "user", "content": body})

    try:
        response = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply_text = response.content[0].text
    except Exception as e:
        reply_text = f"Error: {e}"

    history.append({"role": "assistant", "content": reply_text})

    # Trim history to avoid token bloat
    if len(history) > MAX_HISTORY:
        conversations[from_number] = history[-MAX_HISTORY:]

    return _reply(reply_text)


def _reply(text):
    resp = MessagingResponse()
    resp.message(text)
    return str(resp), 200, {"Content-Type": "text/xml"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
