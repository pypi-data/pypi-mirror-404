from django.contrib import admin

from .models import UserToken


@admin.register(UserToken)
class UserTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'scope', 'last_used_at', 'expires_at')
    readonly_fields = ('key',)
