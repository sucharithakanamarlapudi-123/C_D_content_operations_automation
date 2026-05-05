from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Content_Auditng_Tool"
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    OPENAI_API_VERSION: str
    AZURE_OPENAI_LLM_DEPLOYMENT: str
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str
    VECTOR_DB_PATH: str = "./vector_db"
    PROJECT_NAME: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
