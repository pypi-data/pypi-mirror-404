from django.core.management.base import BaseCommand

from saas.registry import perm_registry


class Command(BaseCommand):
    help = 'Show current registered permissions, roles, and scopes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--permissions',
            action='store_true',
            help='Show all registered permissions',
        )
        parser.add_argument(
            '--roles',
            action='store_true',
            help='Show all registered roles',
        )
        parser.add_argument(
            '--scopes',
            action='store_true',
            help='Show all registered scopes',
        )

    def handle(self, *args, **options):
        show_all = not (options['permissions'] or options['roles'] or options['scopes'])

        if show_all or options['permissions']:
            self.show_permissions()
            self.stdout.write('')

        if show_all or options['roles']:
            self.show_roles()
            self.stdout.write('')

        if show_all or options['scopes']:
            self.show_scopes()
            self.stdout.write('')

    def show_permissions(self):
        self.stdout.write(self.style.SUCCESS('Permissions:'))
        permissions = sorted(perm_registry.get_permission_list(), key=lambda p: p.key)
        if not permissions:
            self.stdout.write('  (None)')
            return

        # Simple formatting
        for perm in permissions:
            self.stdout.write(f'  {self.style.MIGRATE_LABEL(perm.key)}')
            self.stdout.write(f'    Module: {perm.module}, Severity: {perm.severity}')
            self.stdout.write(f'    Label: {perm.label}')
            if perm.description:
                self.stdout.write(f'    Description: {perm.description}')
            self.stdout.write('')

    def show_roles(self):
        self.stdout.write(self.style.SUCCESS('Roles:'))
        roles = sorted(perm_registry.get_role_list(), key=lambda r: r.code)
        if not roles:
            self.stdout.write('  (None)')
            return

        for role in roles:
            self.stdout.write(f'  {self.style.MIGRATE_LABEL(role.code)} ({role.name})')
            if role.description:
                self.stdout.write(f'    Description: {role.description}')

            perms = sorted(role.permissions)
            if perms:
                self.stdout.write('    Permissions:')
                for p in perms:
                    self.stdout.write(f'      - {p}')
            else:
                self.stdout.write('    Permissions: (None)')
            self.stdout.write('')

    def show_scopes(self):
        self.stdout.write(self.style.SUCCESS('Scopes:'))
        scopes = sorted(perm_registry.get_scope_list(), key=lambda s: s.key)
        if not scopes:
            self.stdout.write('  (None)')
            return

        for scope in scopes:
            self.stdout.write(f'  {self.style.MIGRATE_LABEL(scope.key)}')
            self.stdout.write(f'    Label: {scope.label}')
            if scope.is_oidc:
                self.stdout.write('    Type: OIDC')
            if scope.description:
                self.stdout.write(f'    Description: {scope.description}')

            perms = sorted(scope.permissions)
            if perms:
                self.stdout.write('    Permissions:')
                for p in perms:
                    self.stdout.write(f'      - {p}')
            else:
                self.stdout.write('    Permissions: (None)')
            self.stdout.write('')
