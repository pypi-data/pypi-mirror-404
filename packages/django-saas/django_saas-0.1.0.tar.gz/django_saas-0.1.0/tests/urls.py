from django.urls import include, path
from drf_spectacular.views import SpectacularJSONAPIView

from saas.tenancy import api_urls as tenancy_urls

urlpatterns = [
    path('m/', include('saas.api_urls')),
    path('m/sso/', include('saas.sso.auth_urls')),
    path('m/', include('tests.demo_app.urls')),
    path('v/', include('saas.identity.urls')),
    path('tenant/<tenant_id>/members/', include(tenancy_urls.member_urls)),
    path('schema/openapi', SpectacularJSONAPIView.as_view(), name='schema'),
]
