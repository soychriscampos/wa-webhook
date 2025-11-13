# wa_send.py
import os
import requests

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
