from rest_framework import serializers

from saas.registry import perm_registry

from .models import UserToken


class UserTokenSerializer(serializers.ModelSerializer):
    last_used = serializers.IntegerField(source='get_last_used', read_only=True, allow_null=True)

    class Meta:
        model = UserToken
        exclude = ['user']
        extra_kwargs = {
            'key': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def validate_scope(self, value: str):
        scopes = value.split(' ')
        inclusion_map = perm_registry.get_scope_inclusion_map()

        to_remove = set()
        for s_key in scopes:
            if s_key not in inclusion_map:
                raise serializers.ValidationError(f'Scope {s_key} is not defined')
            to_remove.update(inclusion_map[s_key])

        return ' '.join([s for s in scopes if s not in to_remove])
