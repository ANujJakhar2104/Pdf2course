from supabase import create_client, Client

from app.core.config import settings

# service_role key -> backend has full access to storage/db, bypasses RLS.
# Never expose this key to the frontend.
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)
