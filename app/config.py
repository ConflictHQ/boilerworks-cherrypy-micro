import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.database_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5440/boilerworks")
        self.port = int(os.environ.get("PORT", "8083"))
        self.api_key_seed = os.environ.get("API_KEY_SEED", "")
