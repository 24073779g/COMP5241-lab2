from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables from a local .env during development.
# In production (Vercel) environment variables should be set in the project settings
# and no .env file will be present. We avoid raising during import so serverless
# functions don't crash at startup if env vars aren't configured.
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")


class _MissingSupabaseClient:
    """Fallback object returned when Supabase env vars are missing.

    Any attribute access returns a callable which will raise a RuntimeError when invoked.
    This prevents import-time crashes but surfaces a clear error at request time.
    """
    def __getattr__(self, name):
        def _raise(*args, **kwargs):
            raise RuntimeError(
                "Supabase client not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY "
                "in environment variables (e.g. in Vercel project settings)."
            )
        return _raise


if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
else:
    # Do not raise here — allow the app to start and return informative errors when
    # a route actually tries to use Supabase.
    supabase = _MissingSupabaseClient()