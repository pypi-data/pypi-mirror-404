from django.db import transaction
from rest_framework.request import Request
from rest_framework.response import Response

from saas.drf.decorators import resource_permission
from saas.drf.views import AuthenticatedEndpoint

from ..models import Invitation
from ..serializers.invitation import InvitationInfoSerializer, InvitationReceiveSerializer

__all__ = [
    'UserInvitationListEndpoint',
    'UserInvitationAcceptEndpoint',
]


class UserInvitationListEndpoint(AuthenticatedEndpoint):
    serializer_class = InvitationInfoSerializer
    queryset = Invitation.objects.select_related('tenant', 'inviter').all()
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset.filter(email=self.request.user.email)
        return queryset.filter(status=Invitation.InviteStatus.SENT)

    @resource_permission('user.org.view')
    def get(self, request: Request, *args, **kwargs):
        """List all the current user's invitations."""
        queryset = self.filter_queryset(self.get_queryset())

        items = []
        with transaction.atomic():
            for invitation in queryset:
                if invitation.is_expired():
                    invitation.status = Invitation.InviteStatus.EXPIRED
                    invitation.save()
                else:
                    items.append(invitation)

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class UserInvitationAcceptEndpoint(AuthenticatedEndpoint):
    serializer_class = InvitationReceiveSerializer
    queryset = Invitation.objects.all()

    @resource_permission('user.org.join')
    def patch(self, request: Request, *args, **kwargs):
        obj: Invitation = self.get_object()
        serializer = self.get_serializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = InvitationInfoSerializer(obj)
        return Response(serializer.data)
