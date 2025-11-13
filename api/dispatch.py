# api/dispatch.py
from datetime import datetime
from flask import Flask, request, jsonify
from supa_client import get_supa
from wa_send import send_template

app = Flask(__name__)

@app.post("/api/dispatch")
def dispatch():
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
        return jsonify({"ok": True, "processed": 0})

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
            vars_list = row["vars"] if isinstance(row["vars"], list) else []

            # Enviar mensaje vía WhatsApp
            send_template(to, template_name, vars_list)

            # Marcar como enviado
            supa.table("wa_outbox").update({
                "status": "SENT",
                "sent_at": datetime.utcnow().isoformat(),
                "last_error": None
            }).eq("id", wid).execute()

            processed += 1

        except Exception as e:
            new_status = "ERROR" if attempts + 1 >= 5 else "PENDING"
            supa.table("wa_outbox").update({
                "status": new_status,
                "last_error": str(e)
            }).eq("id", wid).execute()

    return jsonify({"ok": True, "processed": processed})
