from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema
from rest_framework import serializers

from saas.identity.serializers.invitation import (
    InvitationInfoSerializer,
    InvitationSerializer,
)
from saas.identity.serializers.tenant import (
    TenantSerializer,
    TenantUpdateSerializer,
)
from saas.identity.serializers.user import UserSerializer
from saas.identity.serializers.user_email import UserEmailSerializer
from saas.identity.serializers.user_tenant import UserTenantSerializer
from saas.internals.serializers import (
    PermissionSerializer,
    RoleSerializer,
    ScopeSerializer,
)
from saas.tenancy.serializers.group import GroupSerializer
from saas.tenancy.serializers.member import (
    MemberSerializer,
    MemberUpdateSerializer,
)


class AuthResponseSerializer(serializers.Serializer):
    next = serializers.CharField()


class FixedPermissionEndpoint(OpenApiViewExtension):
    target_class = 'saas.internals.endpoints.PermissionListEndpoint'

    def view_replacement(self):
        class PermissionListEndpoint(self.target_class):
            @extend_schema(tags=['Config'], summary='All Permissions', responses={200: PermissionSerializer})
            def get(self, *args, **kwargs):
                pass

        return PermissionListEndpoint


class FixedRoleEndpoint(OpenApiViewExtension):
    target_class = 'saas.internals.endpoints.RoleListEndpoint'

    def view_replacement(self):
        class RoleListEndpoint(self.target_class):
            @extend_schema(tags=['Config'], summary='All Roles', responses={200: RoleSerializer})
            def get(self, *args, **kwargs):
                pass

        return RoleListEndpoint


class FixedScopeEndpoint(OpenApiViewExtension):
    target_class = 'saas.internals.endpoints.ScopeListEndpoint'

    def view_replacement(self):
        class RoleListEndpoint(self.target_class):
            @extend_schema(tags=['Config'], summary='All Scopes', responses={200: ScopeSerializer})
            def get(self, *args, **kwargs):
                pass

        return RoleListEndpoint


class FixedPasswordLogInEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.auth.PasswordLogInEndpoint'

    def view_replacement(self):
        class PasswordLogInEndpoint(self.target_class):
            @extend_schema(tags=['Auth'], summary='Log In', responses={200: AuthResponseSerializer})
            def post(self, *args, **kwargs):
                pass

        return PasswordLogInEndpoint


class FixedLogoutEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.auth.LogoutEndpoint'

    def view_replacement(self):
        class LogoutEndpoint(self.target_class):
            @extend_schema(tags=['Auth'], summary='Log Out', request=None, responses={200: AuthResponseSerializer})
            def post(self, *args, **kwargs):
                pass

        return LogoutEndpoint


class FixedSignupConfirmEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.auth.SignupConfirmEndpoint'

    def view_replacement(self):
        class SignupConfirmEndpoint(self.target_class):
            @extend_schema(tags=['Auth'], summary='Sign Up', responses={200: AuthResponseSerializer})
            def post(self, *args, **kwargs):
                pass

        return SignupConfirmEndpoint


class FixedSignupRequestEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.auth.SignupRequestEndpoint'

    def view_replacement(self):
        class SignupRequestEndpoint(self.target_class):
            @extend_schema(tags=['Auth'], summary='Request to Sign-up', responses={204: None})
            def post(self, *args, **kwargs):
                pass

        return SignupRequestEndpoint


class FixedSignupWithInvitationEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.auth.SignupWithInvitationEndpoint'

    def view_replacement(self):
        class SignupWithInvitationEndpoint(self.target_class):
            @extend_schema(tags=['Auth'], summary='Sign Up with Invitation', responses={200: AuthResponseSerializer})
            def post(self, *args, **kwargs):
                pass

        return SignupWithInvitationEndpoint


class FixedInvitationEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.auth.InvitationEndpoint'

    def view_replacement(self):
        class InvitationEndpoint(self.target_class):
            @extend_schema(tags=['Auth'], summary='View Invitation', responses={200: InvitationInfoSerializer})
            def get(self, *args, **kwargs):
                pass

        return InvitationEndpoint


class FixedPasswordResetEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.password.PasswordResetEndpoint'

    def view_replacement(self):
        class PasswordResetEndpoint(self.target_class):
            @extend_schema(tags=['Auth'], summary='Password Reset', responses={200: AuthResponseSerializer})
            def post(self, *args, **kwargs):
                pass

        return PasswordResetEndpoint


class FixedPasswordForgotEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.password.PasswordForgotEndpoint'

    def view_replacement(self):
        class PasswordForgotEndpoint(self.target_class):
            @extend_schema(tags=['Auth'], summary='Password Forgot', responses={204: None})
            def post(self, *args, **kwargs):
                pass

        return PasswordForgotEndpoint


class FixedUserEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.user.UserEndpoint'

    def view_replacement(self):
        class UserEndpoint(self.target_class):
            @extend_schema(tags=['User'], summary='Current User', responses={200: UserSerializer})
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['User'], summary='Update User', responses={200: UserSerializer})
            def patch(self, *args, **kwargs):
                pass

        return UserEndpoint


class FixedUserPasswordEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.user.UserPasswordEndpoint'

    def view_replacement(self):
        class UserPasswordEndpoint(self.target_class):
            @extend_schema(tags=['User'], summary='Update Password')
            def post(self, *args, **kwargs):
                pass

        return UserPasswordEndpoint


class FixedUserEmailListEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.user_emails.UserEmailListEndpoint'

    def view_replacement(self):
        class UserEmailListEndpoint(self.target_class):
            @extend_schema(tags=['User'], summary='List Emails', responses={200: UserEmailSerializer(many=True)})
            def get(self, *args, **kwargs):
                pass

        return UserEmailListEndpoint


class FixedUserEmailItemEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.user_emails.UserEmailItemEndpoint'

    def view_replacement(self):
        class UserEmailItemEndpoint(self.target_class):
            @extend_schema(tags=['User'], summary='View Email Details', responses={200: UserEmailSerializer})
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['User'], summary='Update Email', responses={200: UserEmailSerializer})
            def patch(self, *args, **kwargs):
                pass

            @extend_schema(tags=['User'], summary='Delete Email', responses={204: None})
            def delete(self, *args, **kwargs):
                pass

        return UserEmailItemEndpoint


class FixedAddUserEmailRequestEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.user_emails.AddUserEmailRequestEndpoint'

    def view_replacement(self):
        class AddUserEmailRequestEndpoint(self.target_class):
            @extend_schema(tags=['User'], summary='Request Add Email', responses={204: None})
            def post(self, *args, **kwargs):
                pass

        return AddUserEmailRequestEndpoint


class FixedAddUserEmailConfirmEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.user_emails.AddUserEmailConfirmEndpoint'

    def view_replacement(self):
        class AddUserEmailConfirmEndpoint(self.target_class):
            @extend_schema(tags=['User'], summary='Confirm Add Email', responses={200: UserEmailSerializer})
            def post(self, *args, **kwargs):
                pass

        return AddUserEmailConfirmEndpoint


class FixedUserInvitationListEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.user_invitations.UserInvitationListEndpoint'

    def view_replacement(self):
        class UserInvitationListEndpoint(self.target_class):
            @extend_schema(
                tags=['User'], summary='List Invitations', responses={200: InvitationInfoSerializer(many=True)}
            )
            def get(self, *args, **kwargs):
                pass

        return UserInvitationListEndpoint


class FixedUserInvitationAcceptEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.user_invitations.UserInvitationAcceptEndpoint'

    def view_replacement(self):
        class UserInvitationAcceptEndpoint(self.target_class):
            @extend_schema(tags=['User'], summary='Accept Invitation', responses={200: InvitationInfoSerializer})
            def patch(self, *args, **kwargs):
                pass

        return UserInvitationAcceptEndpoint


class FixedUserTenantListEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.user_tenants.UserTenantListEndpoint'

    def view_replacement(self):
        class UserTenantListEndpoint(self.target_class):
            @extend_schema(tags=['User'], summary='List Tenants', responses={200: UserTenantSerializer(many=True)})
            def get(self, *args, **kwargs):
                pass

        return UserTenantListEndpoint


class FixedUserTenantItemEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.user_tenants.UserTenantItemEndpoint'

    def view_replacement(self):
        class UserTenantItemEndpoint(self.target_class):
            @extend_schema(tags=['User'], summary='Leave Tenant', responses={204: None})
            def delete(self, *args, **kwargs):
                pass

        return UserTenantItemEndpoint


class FixedSelectedTenantEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.tenant.SelectedTenantEndpoint'

    def view_replacement(self):
        class SelectedTenantEndpoint(self.target_class):
            @extend_schema(tags=['Tenant'], summary='Current Tenant', responses={200: TenantSerializer})
            def get(self, *args, **kwargs):
                pass

        return SelectedTenantEndpoint


class FixedTenantListEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.tenant.TenantListEndpoint'

    def view_replacement(self):
        class TenantListEndpoint(self.target_class):
            @extend_schema(tags=['Tenant'], summary='List Tenants', responses={200: TenantSerializer(many=True)})
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Tenant'], summary='Create Tenant', responses={201: TenantSerializer})
            def post(self, *args, **kwargs):
                pass

        return TenantListEndpoint


class FixedTenantItemEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.tenant.TenantItemEndpoint'

    def view_replacement(self):
        class TenantItemEndpoint(self.target_class):
            @extend_schema(tags=['Tenant'], summary='Tenant Details', responses={200: TenantUpdateSerializer})
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Tenant'], summary='Update Tenant', responses={200: TenantUpdateSerializer})
            def patch(self, *args, **kwargs):
                pass

        return TenantItemEndpoint


class FixedTenantTransferEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.tenant.TenantTransferEndpoint'

    def view_replacement(self):
        class TenantTransferEndpoint(self.target_class):
            @extend_schema(tags=['Tenant'], summary='Transfer Tenant', responses={204: None})
            def post(self, *args, **kwargs):
                pass

        return TenantTransferEndpoint


class FixedTenantDestroyEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.tenant.TenantDestroyEndpoint'

    def view_replacement(self):
        class TenantDestroyEndpoint(self.target_class):
            @extend_schema(tags=['Tenant'], summary='Destroy Tenant', responses={204: None})
            def post(self, *args, **kwargs):
                pass

        return TenantDestroyEndpoint


class FixedInvitationListEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.invitations.InvitationListEndpoint'

    def view_replacement(self):
        class InvitationListEndpoint(self.target_class):
            @extend_schema(
                tags=['Tenant'], summary='List Invitations', responses={200: InvitationSerializer(many=True)}
            )
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Tenant'], summary='Invite Member', responses={201: InvitationSerializer})
            def post(self, *args, **kwargs):
                pass

        return InvitationListEndpoint


class FixedInvitationItemEndpoint(OpenApiViewExtension):
    target_class = 'saas.identity.endpoints.invitations.InvitationItemEndpoint'

    def view_replacement(self):
        class InvitationItemEndpoint(self.target_class):
            @extend_schema(tags=['Tenant'], summary='Update Invitation', responses={200: InvitationSerializer})
            def patch(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Tenant'], summary='Delete Invitation', responses={204: None})
            def delete(self, *args, **kwargs):
                pass

        return InvitationItemEndpoint


class FixedGroupListEndpoint(OpenApiViewExtension):
    target_class = 'saas.tenancy.endpoints.groups.GroupListEndpoint'

    def view_replacement(self):
        class GroupListEndpoint(self.target_class):
            @extend_schema(tags=['Tenancy'], summary='List Groups', responses={200: GroupSerializer(many=True)})
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Tenancy'], summary='Create Group', responses={201: GroupSerializer})
            def post(self, *args, **kwargs):
                pass

        return GroupListEndpoint


class FixedGroupItemEndpoint(OpenApiViewExtension):
    target_class = 'saas.tenancy.endpoints.groups.GroupItemEndpoint'

    def view_replacement(self):
        class GroupItemEndpoint(self.target_class):
            @extend_schema(tags=['Tenancy'], summary='Group Details', responses={200: GroupSerializer})
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Tenancy'], summary='Update Group', responses={200: GroupSerializer})
            def put(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Tenancy'], summary='Partial Update Group', responses={200: GroupSerializer})
            def patch(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Tenancy'], summary='Delete Group', responses={204: None})
            def delete(self, *args, **kwargs):
                pass

        return GroupItemEndpoint


class FixedMemberListEndpoint(OpenApiViewExtension):
    target_class = 'saas.tenancy.endpoints.members.MemberListEndpoint'

    def view_replacement(self):
        class MemberListEndpoint(self.target_class):
            @extend_schema(tags=['Tenancy'], summary='List Members', responses={200: MemberSerializer(many=True)})
            def get(self, *args, **kwargs):
                pass

        return MemberListEndpoint


class FixedMemberItemEndpoint(OpenApiViewExtension):
    target_class = 'saas.tenancy.endpoints.members.MemberItemEndpoint'

    def view_replacement(self):
        class MemberItemEndpoint(self.target_class):
            @extend_schema(tags=['Tenancy'], summary='Update Member', responses={200: MemberUpdateSerializer})
            def patch(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Tenancy'], summary='Remove Member', responses={204: None})
            def delete(self, *args, **kwargs):
                pass

        return MemberItemEndpoint
