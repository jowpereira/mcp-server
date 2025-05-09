import re
import logging

logger = logging.getLogger(__name__)

class PasswordValidator:
    """
    Classe para validação de segurança de senhas.
    Implementa regras para garantir que senhas sigam boas práticas de segurança.
    """
    
    # Configurações padrão
    DEFAULT_MIN_LENGTH = 8
    DEFAULT_REQUIRE_UPPERCASE = True
    DEFAULT_REQUIRE_LOWERCASE = True
    DEFAULT_REQUIRE_DIGITS = True
    DEFAULT_REQUIRE_SPECIAL = True
    DEFAULT_MIN_UNIQUE_CHARS = 4
    DEFAULT_DISALLOW_COMMON = True
    
    # Lista de senhas comuns mais utilizadas (pode ser expandida)
    COMMON_PASSWORDS = [
        "123456", "password", "123456789", "12345678", "12345", 
        "1234567890", "qwerty", "abc123", "admin", "welcome",
        "monkey", "login", "passw0rd", "qwerty123", "letmein",
        "welcome1", "password1", "1234", "123123", "test"
    ]
    
    def __init__(self, 
                 min_length=DEFAULT_MIN_LENGTH,
                 require_uppercase=DEFAULT_REQUIRE_UPPERCASE,
                 require_lowercase=DEFAULT_REQUIRE_LOWERCASE,
                 require_digits=DEFAULT_REQUIRE_DIGITS,
                 require_special=DEFAULT_REQUIRE_SPECIAL,
                 min_unique_chars=DEFAULT_MIN_UNIQUE_CHARS,
                 disallow_common=DEFAULT_DISALLOW_COMMON):
        """
        Inicializa o validador com as regras especificadas.
        
        Args:
            min_length: Tamanho mínimo da senha
            require_uppercase: Se requere pelo menos uma letra maiúscula
            require_lowercase: Se requere pelo menos uma letra minúscula
            require_digits: Se requere pelo menos um dígito
            require_special: Se requere pelo menos um caractere especial
            min_unique_chars: Número mínimo de caracteres únicos
            disallow_common: Se deve verificar senhas comuns
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.min_unique_chars = min_unique_chars
        self.disallow_common = disallow_common
    
    def validate(self, password):
        """
        Valida uma senha contra todas as regras configuradas.
        
        Args:
            password: A senha a ser validada
            
        Returns:
            tuple: (válida, mensagem) onde válida é um booleano e mensagem
                   é uma string vazia se válida ou a descrição do erro se inválida
        """
        # Verificar tamanho mínimo
        if len(password) < self.min_length:
            return False, f"A senha deve ter pelo menos {self.min_length} caracteres."
        
        # Verificar caracteres maiúsculos
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            return False, "A senha deve conter pelo menos uma letra maiúscula."
        
        # Verificar caracteres minúsculos
        if self.require_lowercase and not re.search(r'[a-z]', password):
            return False, "A senha deve conter pelo menos uma letra minúscula."
        
        # Verificar dígitos
        if self.require_digits and not re.search(r'\d', password):
            return False, "A senha deve conter pelo menos um dígito."
        
        # Verificar caracteres especiais
        if self.require_special and not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|]', password):
            return False, "A senha deve conter pelo menos um caractere especial."
        
        # Verificar número de caracteres únicos
        if len(set(password)) < self.min_unique_chars:
            return False, f"A senha deve conter pelo menos {self.min_unique_chars} caracteres únicos."
        
        # Verificar senhas comuns
        if self.disallow_common and password.lower() in self.COMMON_PASSWORDS:
            return False, "Esta senha é muito comum e facilmente adivinhável."
        
        return True, ""
    
    def get_requirements_text(self):
        """
        Retorna uma string formatada com os requisitos de senha.
        
        Returns:
            str: Texto descrevendo os requisitos de senha
        """
        requirements = [
            f"Pelo menos {self.min_length} caracteres de comprimento",
            "Pelo menos uma letra maiúscula" if self.require_uppercase else None,
            "Pelo menos uma letra minúscula" if self.require_lowercase else None,
            "Pelo menos um dígito" if self.require_digits else None,
            "Pelo menos um caractere especial" if self.require_special else None,
            f"Pelo menos {self.min_unique_chars} caracteres únicos" if self.min_unique_chars > 1 else None,
            "Não pode ser uma senha comumente utilizada" if self.disallow_common else None
        ]
        
        # Filtrar requisitos que são None
        requirements = [req for req in requirements if req is not None]
        
        # Formatar o texto final
        text = "Requisitos de senha:\n"
        for i, req in enumerate(requirements, 1):
            text += f"{i}. {req}\n"
        
        return text


# Instância padrão para uso em toda a aplicação
default_validator = PasswordValidator()


def validate_password(password, return_all_errors=False):
    """
    Função de conveniência para validar senhas com configurações padrão.
    
    Args:
        password: A senha a ser validada
        return_all_errors: Se True, retorna uma lista de todas as falhas de validação
                           Se False, retorna apenas o primeiro erro encontrado
        
    Returns:
        tuple: (válida, mensagem/mensagens)
    """
    if return_all_errors:
        errors = []
        
        # Validar cada critério separadamente
        if len(password) < PasswordValidator.DEFAULT_MIN_LENGTH:
            errors.append(f"A senha deve ter pelo menos {PasswordValidator.DEFAULT_MIN_LENGTH} caracteres.")
        
        if PasswordValidator.DEFAULT_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("A senha deve conter pelo menos uma letra maiúscula.")
        
        if PasswordValidator.DEFAULT_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("A senha deve conter pelo menos uma letra minúscula.")
        
        if PasswordValidator.DEFAULT_REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("A senha deve conter pelo menos um dígito.")
        
        if PasswordValidator.DEFAULT_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|]', password):
            errors.append("A senha deve conter pelo menos um caractere especial.")
        
        if len(set(password)) < PasswordValidator.DEFAULT_MIN_UNIQUE_CHARS:
            errors.append(f"A senha deve conter pelo menos {PasswordValidator.DEFAULT_MIN_UNIQUE_CHARS} caracteres únicos.")
        
        if PasswordValidator.DEFAULT_DISALLOW_COMMON and password.lower() in PasswordValidator.COMMON_PASSWORDS:
            errors.append("Esta senha é muito comum e facilmente adivinhável.")
        
        return len(errors) == 0, errors
    else:
        # Usar o validador padrão para retornar apenas o primeiro erro
        return default_validator.validate(password)
