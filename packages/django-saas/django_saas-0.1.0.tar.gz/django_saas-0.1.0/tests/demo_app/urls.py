from django.urls import path

from .views import TenantSecretItemEndpoint, TenantSecretListEndpoint

urlpatterns = [
    path('secrets/', TenantSecretListEndpoint.as_view()),
    path('secrets/<pk>/', TenantSecretItemEndpoint.as_view()),
]
