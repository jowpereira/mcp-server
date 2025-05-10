import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Verifica se estamos em ambiente de teste
is_testing = 'pytest' in sys.modules

# Define os caminhos para os arquivos .env
env_test_path = Path('.') / '.env.test'
env_path = Path('.') / '.env'

# Prioridade para o ambiente de teste
if is_testing:
    print(f"Executando em ambiente de teste.")
    if env_test_path.exists():
        print(f"Carregando variáveis de ambiente de teste: {env_test_path.absolute()}")
        load_dotenv(dotenv_path=env_test_path, override=True)
    else:
        print(f"AVISO: Arquivo .env.test não encontrado em {env_test_path.absolute()}!")
        if env_path.exists():
            print(f"Carregando variáveis de .env em ambiente de teste: {env_path.absolute()}")
            load_dotenv(dotenv_path=env_path, override=True)
else:
    # Ambiente normal (não-teste)
    if env_path.exists():
        print(f"Carregando variáveis de ambiente de: {env_path.absolute()}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        print(f"AVISO: Arquivo .env não encontrado em {env_path.absolute()}!")

class Settings:
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'changeme')
    RBAC_FILE: str = os.getenv('RBAC_FILE', str(Path(__file__).parent.parent / 'data' / 'rbac.json'))

    def __init__(self):
        # Exibe informações de diagnóstico na inicialização
        print(f"CONFIG: SECRET_KEY definida como: {self.SECRET_KEY[:5]}{'*' * 10}")
        print(f"CONFIG: RBAC_FILE definido como: {self.RBAC_FILE}")

settings = Settings()
