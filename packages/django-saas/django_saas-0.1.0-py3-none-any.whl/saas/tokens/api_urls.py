from django.urls import path

from .endpoints import UserTokenItemEndpoint, UserTokenListEndpoint

urlpatterns = [
    path('', UserTokenListEndpoint.as_view()),
    path('<int:pk>/', UserTokenItemEndpoint.as_view()),
]
