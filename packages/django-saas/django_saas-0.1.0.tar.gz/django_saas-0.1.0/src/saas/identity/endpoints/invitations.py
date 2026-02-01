from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response

from saas.drf.decorators import resource_permission
from saas.drf.filters import IncludeFilter, TenantIdFilter
from saas.drf.views import TenantEndpoint
from saas.identity.settings import identity_settings
from saas.identity.signals import invitation_created
from saas.signals import mail_queued

from ..models import Invitation
from ..serializers.invitation import InvitationSerializer

__all__ = [
    'InvitationListEndpoint',
    'InvitationItemEndpoint',
]


class InvitationListEndpoint(ListModelMixin, TenantEndpoint):
    email_template_id = 'invite_member'
    email_subject = _("You've Been Invited to Join %s")

    serializer_class = InvitationSerializer
    filter_backends = [TenantIdFilter, IncludeFilter]
    queryset = Invitation.objects.all()
    pagination_class = None

    include_select_related_fields = ['role']
    include_prefetch_related_fields = ['groups']

    invitation_accept_url = 'saas_identity:invitation-accept'

    def get_queryset(self):
        return self.queryset.filter(status__lt=Invitation.InviteStatus.ACCEPTED)

    def get_email_subject(self):
        return self.email_subject % str(self.request.tenant)

    def get_invitation_accept_url(self, invitation: Invitation) -> str:
        kwargs = {'token': invitation.token}
        if identity_settings.INVITATION_ACCEPT_URL:
            return identity_settings.INVITATION_ACCEPT_URL.format(**kwargs)
        return reverse(self.invitation_accept_url, kwargs=kwargs)

    @resource_permission('iam.member.view')
    def get(self, request: Request, *args, **kwargs):
        """List all members in the tenant."""
        return self.list(request, *args, **kwargs)

    @resource_permission('iam.member.invite')
    def post(self, request: Request, *args, **kwargs):
        """Invite a member to join the tenant."""
        tenant_id = self.get_tenant_id()
        context = self.get_serializer_context()
        serializer = InvitationSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save(tenant_id=tenant_id, inviter=request.user)

        invitation_created.send(self.__class__, member=invitation, request=request)

        invite_link = self.get_invitation_accept_url(invitation)
        if not invite_link.startswith('http'):
            invite_link = request.build_absolute_uri(invite_link)

        mail_queued.send(
            sender=self.__class__,
            template_id=self.email_template_id,
            subject=str(self.get_email_subject()),
            recipients=[invitation.email],
            context={
                'inviter': request.user,
                'member': invitation,
                'tenant': request.tenant,
                'invite_link': invite_link,
            },
            request=request,
        )
        return Response(serializer.data, status=201)


class InvitationItemEndpoint(UpdateModelMixin, DestroyModelMixin, TenantEndpoint):
    serializer_class = InvitationSerializer
    queryset = Invitation.objects.all()

    @resource_permission('iam.member.update')
    def patch(self, request: Request, *args, **kwargs):
        """Update an invitation's role and groups."""
        return self.partial_update(request, *args, **kwargs)

    @resource_permission('iam.member.delete')
    def delete(self, request: Request, *args, **kwargs):
        """Remove an invitation from the tenant."""
        return self.destroy(request, *args, **kwargs)
