from django.contrib import admin
from django.utils.html import mark_safe

from saas.registry import perm_registry

from .models import (
    Invitation,
    Membership,
    UserEmail,
    UserProfile,
)


@admin.register(UserEmail)
class UserEmailAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'primary', 'verified', 'created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['avatar', 'user', 'region', 'locale', 'timezone']
    list_display_links = ['user']

    def avatar(self, obj: UserProfile):
        if not obj.avatar_url:
            return '-'
        if obj.avatar_url.startswith('https://'):
            return mark_safe(f'<img src="{obj.avatar_url}" width="32" height="32" />')
        return obj.avatar_url


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'email', 'role', 'created_at']
    readonly_fields = ['permissions']

    def permissions(self, obj: Invitation):
        perms = perm_registry.get_role(obj.role).permissions
        return ', '.join(perms)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'user', 'role', 'created_at']
    list_filter = ['role']
    readonly_fields = ['permissions']

    def permissions(self, obj: Membership):
        perms = perm_registry.get_role(obj.role).permissions
        return ', '.join(perms)
