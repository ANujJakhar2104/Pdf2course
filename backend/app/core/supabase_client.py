from supabase import create_client, Client

from app.core.config import settings

# service_role key -> backend has full access to storage/db, bypasses RLS.
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)
