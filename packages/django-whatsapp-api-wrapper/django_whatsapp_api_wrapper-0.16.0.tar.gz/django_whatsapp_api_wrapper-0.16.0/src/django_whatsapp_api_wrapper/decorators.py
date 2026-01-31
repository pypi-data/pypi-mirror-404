"""
Decorators for django-whatsapp-api-wrapper.

These decorators make multi-tenancy requirements explicit in the code.
"""
from functools import wraps
from rest_framework.response import Response


def require_tenant(view_func):
    """
    Decorator que VERIFICA se request.tenant_id existe.

    O tenant_id deve ser setado por um middleware do projeto consumidor
    ANTES de chegar neste decorator. Isso permite que este pacote seja
    agnóstico ao modelo de dados do projeto.

    Usage:
        ```python
        # No settings.py do projeto, adicionar TenantMiddleware que seta request.tenant_id

        from django_whatsapp_api_wrapper.decorators import require_tenant

        class MyView(BaseAuthenticatedAPIView):
            @require_tenant  # ← VISÍVEL que esta view precisa de tenant
            def get(self, request):
                # tenant_id está garantido aqui
                tenant_id = request.tenant_id
                # ...
        ```

    Requirements:
        - Usuário deve estar autenticado
        - request.tenant_id deve ser setado por middleware antes de chegar aqui

    Returns:
        401 response se usuário não autenticado
        400 response se tenant_id não foi setado
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        # 1. Verifica se usuário está autenticado
        if not request.user or not request.user.is_authenticated:
            return Response(
                {
                    "error": "Authentication required",
                    "detail": "User must be authenticated to access this endpoint."
                },
                status=401
            )

        # 2. Verifica se tenant_id foi setado (por middleware ou view anterior)
        tenant_id = getattr(request, 'tenant_id', None)
        if tenant_id is None:
            return Response(
                {
                    "error": "Tenant context required",
                    "detail": "request.tenant_id must be set by middleware before "
                             "accessing this endpoint. Ensure TenantMiddleware is "
                             "configured in your Django settings."
                },
                status=400
            )

        # 3. Chama a view original
        return view_func(self, request, *args, **kwargs)

    return wrapper
