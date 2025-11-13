# api/supa_client.py
import os
from supabase import create_client, Client

def get_supa() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]   # <-- usando tu variable
    return create_client(url, key)
