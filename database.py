import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_client: Client = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL or SUPABASE_SERVICE_KEY is not set. "
                "Add them as environment variables in your Vercel project settings."
            )
        _supabase_client = create_client(url, key)
    return _supabase_client


supabase: Client = None


class _LazySupabase:
    def __getattr__(self, name):
        return getattr(get_supabase(), name)


supabase = _LazySupabase()
