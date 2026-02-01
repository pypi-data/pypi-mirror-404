from django.contrib import admin

from .models import (
    Group,
    Member,
)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'tenant', 'name', 'managed', 'created_at']


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'tenant', 'user', 'created_at']
