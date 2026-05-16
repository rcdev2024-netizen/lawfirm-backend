import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError(
        "\n\n❌  SUPABASE_URL or SUPABASE_SERVICE_KEY is missing in .env\n"
        "    Make sure your .env file has both values set.\n"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
