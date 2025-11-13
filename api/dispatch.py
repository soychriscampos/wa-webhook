# api/dispatch.py
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

@app.post("/api/dispatch")
def dispatch():
    try:
        # Importamos aquí para que cualquier error de import/env vars
        # quede atrapado en este try/except.
        from supa_client import get_supa
        from api.wa_send import send_template

        supa = get_supa()

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
        # Aquí atrapamos errores gordos: supabase no instalado, env vars faltantes, etc.
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500
