from django.urls import path

from .endpoints.domain import (
    DomainItemEndpoint,
    DomainListEndpoint,
    DomainVerifyEndpoint,
)

urlpatterns = [
    path('', DomainListEndpoint.as_view()),
    path('<hostname>/', DomainItemEndpoint.as_view()),
    path('<hostname>/verify/', DomainVerifyEndpoint.as_view()),
]
