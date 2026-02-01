from rest_framework.permissions import IsAuthenticated


class NotUseToken(IsAuthenticated):
    """This permission is designed for internal use"""

    def has_permission(self, request, view):
        if request.auth:
            return False
        return super().has_permission(request, view)
