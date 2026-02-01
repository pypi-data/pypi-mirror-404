from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from saas.drf.serializers import ChoiceField, ModelSerializer
from saas.identity.models import Invitation, Membership, UserEmail
from saas.registry import perm_registry

from .tenant import TenantSerializer
from .user import SimpleUserSerializer


class InvitationSerializer(ModelSerializer):
    email = serializers.EmailField(required=True)
    role = serializers.CharField(required=False)

    class Meta:
        model = Invitation
        exclude = ['tenant', 'inviter']
        read_only_fields = ['status', 'accepted_at', 'created_at']

    def validate_role(self, role: str):
        if role not in perm_registry.get_role_codes():
            raise serializers.ValidationError(_('Invalid role.'))
        return role

    def validate_email(self, email: str):
        request = self.context['request']
        if Invitation.objects.filter(tenant_id=request.tenant_id, email=email).exists():
            raise serializers.ValidationError(_('This email has already been invited.'))

        try:
            user_email = UserEmail.objects.get_by_email(email)
        except ObjectDoesNotExist:
            return email

        if Membership.objects.filter(tenant_id=request.tenant_id, user_id=user_email.user_id).exists():
            raise serializers.ValidationError(_('This user is already a member.'))

        return email


class InvitationInfoSerializer(ModelSerializer):
    tenant = TenantSerializer(read_only=True)
    inviter = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = '__all__'


class InvitationReceiveSerializer(ModelSerializer):
    status = ChoiceField(
        choices=[
            (Invitation.InviteStatus.ACCEPTED, Invitation.InviteStatus.ACCEPTED.label),
            (Invitation.InviteStatus.DECLINED, Invitation.InviteStatus.DECLINED.label),
        ]
    )

    class Meta:
        model = Invitation
        fields = ['status']

    def update(self, instance: Invitation, validated_data):
        if validated_data['status'] == Invitation.InviteStatus.ACCEPTED:
            request = self.context['request']
            if not instance.belongs_to_user(request.user):
                raise PermissionDenied('This invitation is not for you.')

            with transaction.atomic():
                instance.accept_invite(request.user)
            return instance
        else:
            instance.status = validated_data['status']
            instance.save()
        return instance
