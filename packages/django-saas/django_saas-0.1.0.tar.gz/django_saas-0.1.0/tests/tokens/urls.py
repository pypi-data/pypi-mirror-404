from django.urls import include, path
from drf_spectacular.views import SpectacularJSONAPIView

urlpatterns = [
    path('api/user/', include('saas.identity.api_urls.user')),
    path('api/user/tokens/', include('saas.tokens.api_urls')),
    path('schema/openapi', SpectacularJSONAPIView.as_view(), name='schema'),
]
