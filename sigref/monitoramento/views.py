from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def verificar_acesso_monitor(view_func):
    """Decorator para verificar se usuário é monitor"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.greuser.is_monitor():
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper

def verificar_acesso_gestor(view_func):
    """Decorator para verificar se usuário é gestor"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.greuser.is_gestor():
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper

def verificar_acesso_setor(setor_requerido):
    """Decorator para verificar acesso a um setor específico"""
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.greuser.is_tecnico_gre() or not request.user.greuser.pode_acessar_setor(setor_requerido):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator