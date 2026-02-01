from django.contrib import admin

from .models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'country', 'user_agent', 'expiry_date', 'last_used')

    def country(self, obj):
        return obj.location.get('country')
