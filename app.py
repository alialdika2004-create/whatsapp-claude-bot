from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "You are a helpful assistant responding to WhatsApp messages. "
        "Keep responses concise and readable on a phone screen."
    )
)

app = Flask(__name__)

# Chat sessions per WhatsApp number
sessions = {}


@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")

    if not body:
        return _reply("(empty message received)")

    if body.lower() in ("/reset", "reset", "/clear", "clear"):
        sessions.pop(from_number, None)
        return _reply("Conversation cleared. Starting fresh!")

    if from_number not in sessions:
        sessions[from_number] = model.start_chat(history=[])

    try:
        response = sessions[from_number].send_message(body)
        reply_text = response.text
    except Exception as e:
        reply_text = f"Error: {e}"

    return _reply(reply_text)


def _reply(text):
    resp = MessagingResponse()
    resp.message(text)
    return str(resp), 200, {"Content-Type": "text/xml"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
