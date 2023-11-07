from rest_framework.permissions import SAFE_METHODS, BasePermission


class AdminOrReadOnly(BasePermission):
    """Разрешение админу. Остальным только чтение."""
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or (
                    request.user.is_active
                    and request.user.is_authenticated
                    and request.user.is_staff
                ))


class AuthorOrAdminOrReadOnly(BasePermission):
    """Разрешение автору. Остальным только чтение."""
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or obj.author == request.user
                or request.user.is_staff)
