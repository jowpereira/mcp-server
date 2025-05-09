import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path('.') / '.env')

class Settings:
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'changeme')
    GROUPS_FILE: str = os.getenv('GROUPS_FILE', str(Path(__file__).parent.parent / 'data' / 'groups.json'))

settings = Settings()
