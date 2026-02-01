from django.urls import path

from .endpoints import (
    PermissionListEndpoint,
    RoleListEndpoint,
    ScopeListEndpoint,
)

urlpatterns = [
    path('permissions/', PermissionListEndpoint.as_view()),
    path('roles/', RoleListEndpoint.as_view()),
    path('scopes/', ScopeListEndpoint.as_view()),
]
