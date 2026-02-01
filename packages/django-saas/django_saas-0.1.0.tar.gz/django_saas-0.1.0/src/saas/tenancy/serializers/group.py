from rest_framework import serializers

from saas.registry import perm_registry
from saas.registry.checker import has_permission

from ..models import Group


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        exclude = ['tenant']
        read_only_fields = ['managed']

    def validate_permissions(self, perms: list[str]):
        registered_perms = perm_registry.get_permission_keys()
        for key in perms:
            if not has_permission(key, registered_perms):
                raise serializers.ValidationError(f'Permission {key} is not registered.')
        return perms
