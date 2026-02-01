from rest_framework import serializers


class PermissionSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    module = serializers.CharField()


class RoleSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    permissions = serializers.ListField(child=serializers.CharField())


class ScopeSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    permissions = serializers.ListField(child=serializers.CharField())
