from django.urls import include, path

urlpatterns = [
    path('m/', include('saas.sso.api_urls')),
    path('m/', include('saas.sso.auth_urls')),
]
