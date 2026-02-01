from rest_framework import serializers

from saas.drf.serializers import FlattenModelSerializer

from ..models import Membership
from .tenant import TenantSerializer


class UserTenantSerializer(FlattenModelSerializer):
    tenant = TenantSerializer(required=True)
    is_owner = serializers.SerializerMethodField()
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Membership
        exclude = ['user', 'id', 'created_at']
        flatten_fields = ['tenant']
        request_include_fields = ['member_count']

    def get_is_owner(self, obj: Membership):
        return obj.tenant.owner_id == obj.user_id
