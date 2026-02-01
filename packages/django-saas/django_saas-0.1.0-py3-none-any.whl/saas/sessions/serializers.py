from rest_framework import serializers

from .models import Session


class SessionSerializer(serializers.ModelSerializer):
    current_session = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = (
            'id',
            'user_agent',
            'expiry_date',
            'last_used',
            'current_session',
            'country',
            'region',
        )

    def get_current_session(self, obj) -> bool:
        request = self.context.get('request')
        if request and request.session.session_key == obj.session_key:
            return True
        return False

    def get_country(self, obj) -> str:
        return obj.location.get('country')

    def get_region(self, obj) -> str:
        return obj.location.get('region')
