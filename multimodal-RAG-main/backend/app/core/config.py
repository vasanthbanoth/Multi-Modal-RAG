from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Pydantic will automatically attempt to load these from the environment
    or from a .env file if python-dotenv is installed.
    """
    # Pinecone settings
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str | None = None
    PINECONE_INDEX_NAME: str = "multi-rag-index"

    # Google Generative AI settings
    GOOGLE_API_KEY: str

    # JWT Authentication settings
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # AWS S3 settings (optional, for file storage)
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    S3_BUCKET_NAME: str | None = None

    class Config:
        # This tells Pydantic to look for a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a single, reusable instance of the settings
# Load values from a local .env file (if present) into the environment
load_dotenv()

# Instantiate settings; Pydantic will read values from environment/.env
settings = Settings()