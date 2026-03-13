import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase_client: Client = None

try:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if url and key and "placeholder" not in url:
        supabase_client = create_client(url, key)
        print("✅ Supabase client initialized successfully")
    else:
        print("⚠️ Supabase credentials missing or placeholders, running in degraded mode")
except Exception as e:
    print(f"❌ Failed to initialize Supabase client: {e}")

def get_supabase():
    return supabase_client
