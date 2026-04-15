import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    ELEVEN_LABS_API_KEY: str = os.getenv("ELEVEN_LABS_API_KEY")
    VOICE_ID: str = os.getenv("VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    PORT: int = int(os.getenv("PORT", 3000))

settings = Settings()