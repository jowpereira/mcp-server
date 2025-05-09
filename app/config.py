import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path('.') / '.env')

class Settings:
    SECRET_KEY: str = 'changeme' # Hardcoded para teste
    RBAC_FILE: str = os.getenv('RBAC_FILE', str(Path(__file__).parent.parent / 'data' / 'rbac.json'))

settings = Settings()
