# api/dispatch.py
import os
import requests
from datetime import datetime
from flask import Flask, jsonify
from supabase import create_client

app = Flask(__name__)

def get_supa():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en las env vars")

    return create_client(url, key)

def send_template(to_whatsapp, template_name, vars_list):
    """
    Envía un template de WhatsApp.
    - template_name: nombre del template en Meta (ej. 'agradecimiento_pago')
    - vars_list: lista de variables de cuerpo en orden.
    """

    token = os.environ.get("META_PERMANENT_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")

    if not token or not phone_number_id:
        raise RuntimeError("Faltan META_PERMANENT_TOKEN o WHATSAPP_PHONE_NUMBER_ID en env vars")

    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_whatsapp,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "es_MX"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": v} for v in vars_list
                    ]
                }
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if not response.ok:
        raise RuntimeError(
            f"Error al enviar WhatsApp: {response.status_code} {response.text}"
        )

    return response.json()

@app.post("/api/dispatch")
def dispatch():
    try:
        supa = get_supa()

        # 1) Leer hasta 10 mensajes pendientes en la outbox
        out = supa.table("wa_outbox") \
            .select("*") \
            .eq("status", "PENDING") \
            .order("created_at", desc=False) \
            .limit(10) \
            .execute()

        rows = out.data or []
        if not rows:
            return jsonify({"ok": True, "processed": 0, "msg": "Sin pendientes"})

        processed = 0

        for row in rows:
            wid = row["id"]
            attempts = int(row.get("attempts", 0))

            # Incrementar contador de intentos
            supa.table("wa_outbox").update({
                "attempts": attempts + 1
            }).eq("id", wid).execute()

            try:
                to = row["to_whatsapp"]
                template_name = row.get("template_name", "agradecimiento_pago")
                vars_list = row.get("vars") or []

                # Enviar mensaje vía WhatsApp
                send_template(to, template_name, vars_list)

                # Marcar como enviado
                supa.table("wa_outbox").update({
                    "status": "SENT",
                    "sent_at": datetime.utcnow().isoformat(),
                    "last_error": None
                }).eq("id", wid).execute()

                processed += 1

            except Exception as inner_e:
                new_status = "ERROR" if attempts + 1 >= 5 else "PENDING"
                supa.table("wa_outbox").update({
                    "status": new_status,
                    "last_error": str(inner_e)
                }).eq("id", wid).execute()

        return jsonify({"ok": True, "processed": processed})
    
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500
