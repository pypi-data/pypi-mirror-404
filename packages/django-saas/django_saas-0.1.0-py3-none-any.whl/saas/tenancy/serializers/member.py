from django.utils.translation import gettext as _
from rest_framework import serializers

from saas.drf.serializers import ModelSerializer, RelatedSerializerField
from saas.identity.serializers.user import UserSerializer
from saas.registry import perm_registry
from saas.registry.checker import has_permission

from ..models import Member
from .group import GroupSerializer


class MemberSerializer(ModelSerializer):
    user = UserSerializer(required=False, read_only=True)
    groups = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    permissions = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Member
        exclude = ['tenant']

    def get_is_owner(self, obj: Member):
        return obj.tenant.owner_id == obj.user_id

    def get_permissions(self, obj: Member):
        assigned_patterns = obj.get_all_permissions()

        all_registered_perms = perm_registry.get_permission_list()
        if self.get_is_owner(obj):
            return [p.key for p in all_registered_perms]

        resolved_keys = [p.key for p in all_registered_perms if has_permission(p.key, assigned_patterns)]
        return resolved_keys


class MemberUpdateSerializer(ModelSerializer):
    groups = RelatedSerializerField(GroupSerializer, many=True)

    class Meta:
        model = Member
        fields = ['role', 'groups', 'permissions']

    def validate_role(self, role: str):
        if role not in perm_registry.get_role_codes():
            raise serializers.ValidationError(_('Invalid role.'))

        # always return OWNER role for owner user
        request = self.context['request']
        if request.tenant.owner_id == self.instance.user_id:
            return 'OWNER'
        return role

    def validate_permissions(self, perms: list[str]):
        registered_perms = perm_registry.get_permission_keys()
        for key in perms:
            if not has_permission(key, registered_perms):
                raise serializers.ValidationError(f'Permission {key} is not registered.')
        return perms
