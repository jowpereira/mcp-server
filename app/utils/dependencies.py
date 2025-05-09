import json
from app.config import settings
from pathlib import Path
from typing import Dict

def get_rbac_data() -> Dict:
    rbac_path = Path(settings.GROUPS_FILE).parent / 'rbac.json'
    with open(rbac_path, 'r', encoding='utf-8') as f:
        return json.load(f)
