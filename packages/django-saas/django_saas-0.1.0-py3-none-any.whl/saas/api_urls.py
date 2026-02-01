from django.urls import include, path

from saas.identity import api_urls as identity_urls
from saas.sso import api_urls as sso_urls
from saas.tenancy import api_urls as tenancy_urls

urlpatterns = [
    path('_/', include('saas.internals.api_urls')),
    path('user/', include(identity_urls.user_urls)),
    path('user/emails/', include(identity_urls.user_email_urls)),
    path('user/tenants/', include(identity_urls.user_tenant_urls)),
    path('user/invitations/', include(identity_urls.user_invitation_urls)),
    path('user/sessions/', include('saas.sessions.api_urls')),
    path('user/tokens/', include('saas.tokens.api_urls')),
    path('sso/', include(sso_urls.sso_urls)),
    path('user/identities/', include(sso_urls.identity_urls)),
    path('domains/', include('saas.domain.api_urls')),
    path('tenants/', include(identity_urls.tenant_urls)),
    path('invitations/', include(identity_urls.invitation_urls)),
    path('auth/', include(identity_urls.auth_urls)),
    path('groups/', include(tenancy_urls.group_urls)),
    path('members/', include(tenancy_urls.member_urls)),
]
