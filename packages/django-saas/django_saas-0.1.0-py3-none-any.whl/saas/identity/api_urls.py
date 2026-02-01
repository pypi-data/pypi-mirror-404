from django.urls import path

from .endpoints.auth import (
    InvitationEndpoint,
    LogoutEndpoint,
    PasswordLogInEndpoint,
    SignupConfirmEndpoint,
    SignupRequestEndpoint,
    SignupWithInvitationEndpoint,
)
from .endpoints.invitations import (
    InvitationItemEndpoint,
    InvitationListEndpoint,
)
from .endpoints.password import (
    PasswordForgotEndpoint,
    PasswordResetEndpoint,
)
from .endpoints.tenant import (
    SelectedTenantEndpoint,
    TenantDestroyEndpoint,
    TenantItemEndpoint,
    TenantListEndpoint,
    TenantTransferEndpoint,
)
from .endpoints.user import UserEndpoint, UserPasswordEndpoint
from .endpoints.user_emails import (
    AddUserEmailConfirmEndpoint,
    AddUserEmailRequestEndpoint,
    UserEmailItemEndpoint,
    UserEmailListEndpoint,
)
from .endpoints.user_invitations import (
    UserInvitationAcceptEndpoint,
    UserInvitationListEndpoint,
)
from .endpoints.user_tenants import (
    UserTenantItemEndpoint,
    UserTenantListEndpoint,
)

auth_urls = [
    path('logout/', LogoutEndpoint.as_view()),
    path('login/', PasswordLogInEndpoint.as_view()),
    path('signup/request/', SignupRequestEndpoint.as_view()),
    path('signup/confirm/', SignupConfirmEndpoint.as_view()),
    path('signup/invite/<token>/', SignupWithInvitationEndpoint.as_view()),
    path('password/forgot/', PasswordForgotEndpoint.as_view()),
    path('password/reset/', PasswordResetEndpoint.as_view()),
    path('invitation/<token>/', InvitationEndpoint.as_view()),
]

invitation_urls = [
    path('', InvitationListEndpoint.as_view()),
    path('<pk>/', InvitationItemEndpoint.as_view()),
]

tenant_urls = [
    path('', TenantListEndpoint.as_view()),
    path('current/', SelectedTenantEndpoint.as_view()),
    path('<pk>/', TenantItemEndpoint.as_view()),
    path('<pk>/transfer/', TenantTransferEndpoint.as_view()),
    path('<pk>/destroy/', TenantDestroyEndpoint.as_view()),
]

user_urls = [
    path('', UserEndpoint.as_view()),
    path('password/', UserPasswordEndpoint.as_view()),
]

user_email_urls = [
    path('', UserEmailListEndpoint.as_view()),
    path('add/request/', AddUserEmailRequestEndpoint.as_view()),
    path('add/confirm/', AddUserEmailConfirmEndpoint.as_view()),
    path('<pk>/', UserEmailItemEndpoint.as_view()),
]

user_invitation_urls = [
    path('', UserInvitationListEndpoint.as_view()),
    path('<pk>/', UserInvitationAcceptEndpoint.as_view()),
]

user_tenant_urls = [
    path('', UserTenantListEndpoint.as_view()),
    path('<tenant_id>/', UserTenantItemEndpoint.as_view()),
]
