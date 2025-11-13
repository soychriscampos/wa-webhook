# api/wa_send.py
import os
import requests

WHATSAPP_TOKEN = os.environ["WHATSAPP_TOKEN"]
PHONE_NUMBER_ID = os.environ["WHATSAPP_PHONE_NUMBER_ID"]

def send_template(to_whatsapp: str, template_name: str, vars_list: list[str]):
    """
    Envía un template de WhatsApp.
    - template_name: nombre del template en Meta (ej. 'agradecimiento_pago')
    - vars_list: lista de variables de cuerpo en orden.
    """

    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    
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
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if not response.ok:
        raise RuntimeError(
            f"Error al enviar WhatsApp: {response.status_code} {response.text}"
        )

    return response.json()
