from django.urls import path

from saas.sso.endpoints.auth import AuthorizedView, LoginView
from saas.sso.endpoints.connect import ConnectAuthorizedView, ConnectRedirectView

app_name = 'saas.sso'

urlpatterns = [
    path('login/<strategy>/', LoginView.as_view(), name='login'),
    path('auth/<strategy>/', AuthorizedView.as_view(), name='auth'),
    path('connect/link/<strategy>/', ConnectRedirectView.as_view()),
    path('connect/auth/<strategy>/', ConnectAuthorizedView.as_view(), name='connect'),
]
