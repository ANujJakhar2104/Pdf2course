from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    supabase_db_url: str
    supabase_anon_key: str 
    supabase_storage_bucket: str = "documents"

    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    frontend_origin: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
