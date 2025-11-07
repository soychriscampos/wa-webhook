import os, hmac, hashlib, json
from flask import Flask, request, Response, abort

app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
APP_SECRET   = os.environ.get("META_APP_SECRET", "")

def verify_signature(raw_body: bytes, signature_header: str) -> bool:
    if not APP_SECRET or not signature_header:
        return True
    try:
        scheme, signature = signature_header.split("=", 1)
        if scheme != "sha256":
            return False
        digest = hmac.new(APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)
    except Exception:
        return False

@app.get("/api/webhook")
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge", "")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(challenge, status=200, mimetype="text/plain")
    return abort(403)

@app.post("/api/webhook")
def receive():
    raw = request.get_data()
    if not verify_signature(raw, request.headers.get("X-Hub-Signature-256", "")):
        return abort(401)
    body = request.get_json(force=True, silent=True) or {}
    print("WA Webhook:", json.dumps(body, ensure_ascii=False))
    return Response("EVENT_RECEIVED", status=200, mimetype="text/plain")
