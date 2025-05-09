import json
from app.config import settings
from pathlib import Path
from typing import Dict
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def get_rbac_data() -> Dict:
    # Corrigido para usar settings.RBAC_FILE em vez de settings.GROUPS_FILE
    rbac_path = Path(settings.RBAC_FILE) 
    try:
        # Assegura que estamos usando o caminho completo definido em RBAC_FILE
        # Não precisamos mais adicionar .parent / 'rbac.json' se RBAC_FILE já é o caminho completo.
        # Se RBAC_FILE for apenas o nome do arquivo e estiver em data/, então o config.py já resolve isso.
        with open(rbac_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Arquivo RBAC não encontrado em: {rbac_path}")
        raise HTTPException(status_code=500, detail=f"Arquivo de configuração RBAC não encontrado: {rbac_path}")
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar o arquivo JSON RBAC em: {rbac_path}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler o arquivo de configuração RBAC (JSON malformado): {rbac_path}")
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar o arquivo RBAC ({rbac_path}): {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao carregar configuração RBAC: {e}")
