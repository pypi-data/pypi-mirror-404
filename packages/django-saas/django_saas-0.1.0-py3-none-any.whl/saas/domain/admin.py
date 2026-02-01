from django.contrib import admin

from .models import Domain


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'hostname', 'provider', 'active', 'created_at')
