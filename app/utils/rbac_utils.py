def is_group_admin_or_global(user, grupo, rbac):
    """
    Verifica se o usuário é admin global ou admin do grupo.
    Retorna True se sim, False caso contrário.
    """
    if user.get("papel") == "global_admin":
        return True
    if grupo in rbac.get("grupos", {}):
        if user.get("username") in rbac["grupos"][grupo].get("admins", []):
            return True
    return False
