from django.urls import path

from .endpoints.identities import (
    UserIdentityItemEndpoint,
    UserIdentityListEndpoint,
)
from .endpoints.session import (
    SessionCreateUserEndpoint,
    SessionUserInfoEndpoint,
)

sso_urls = [
    path('userinfo/', SessionUserInfoEndpoint.as_view()),
    path('create-user/', SessionCreateUserEndpoint.as_view()),
]

identity_urls = [
    path('', UserIdentityListEndpoint.as_view()),
    path('<pk>/', UserIdentityItemEndpoint.as_view()),
]
