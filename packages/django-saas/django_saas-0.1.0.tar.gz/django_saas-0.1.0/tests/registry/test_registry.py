from unittest import TestCase

from saas.registry.registry import Severity, perm_registry


class TestRegistry(TestCase):
    def setUp(self):
        # Reset registry state
        perm_registry._permissions.clear()
        perm_registry._roles.clear()
        perm_registry._scopes.clear()

    def test_register_permission_defaults(self):
        perm_registry.register_permission('test.view', 'View', 'test')
        p = perm_registry._permissions['test.view']
        self.assertEqual(p.severity, Severity.LOW)

        perm_registry.register_permission('test.create', 'Create', 'test')
        p = perm_registry._permissions['test.create']
        self.assertEqual(p.severity, Severity.HIGH)

        perm_registry.register_permission('test.delete', 'Delete', 'test')
        p = perm_registry._permissions['test.delete']
        self.assertEqual(p.severity, Severity.CRITICAL)

        perm_registry.register_permission('test.update', 'Update', 'test')
        p = perm_registry._permissions['test.update']
        self.assertEqual(p.severity, Severity.NORMAL)

    def test_register_duplicate(self):
        perm_registry.register_permission('p1', 'P1', 'mod')
        with self.assertRaises(ValueError):
            perm_registry.register_permission('p1', 'P1', 'mod')

    def test_assign_to_role_creates_role(self):
        perm_registry.assign_to_role('new_role', 'p1')
        self.assertIn('new_role', perm_registry.get_role_codes())
        self.assertIn('p1', perm_registry.get_role('new_role').permissions)

    def test_assign_to_scopes_invalid(self):
        with self.assertRaises(ValueError):
            perm_registry.assign_to_scopes('missing', ['p1'])

    def test_get_scope_inclusion_map(self):
        perm_registry.register_permission('p.view', 'V', 'm')
        perm_registry.register_permission('p.edit', 'E', 'm')

        perm_registry.register_scope('scope.view', 'View', ['p.view'])
        perm_registry.register_scope('scope.edit', 'Edit', ['p.view', 'p.edit'])

        m = perm_registry.get_scope_inclusion_map()

        # scope.edit has {p.view, p.edit}
        # scope.view has {p.view}
        # view is subset of edit.
        # if perms_b (view) is subset of perms_a (edit) -> edit includes view.

        self.assertIn('scope.view', m['scope.edit'])
        self.assertNotIn('scope.edit', m['scope.view'])

    def test_get_permissions_for_scopes(self):
        perm_registry.register_permission('p1', 'P1', 'm')
        perm_registry.register_scope('s1', 'S1', ['p1'])

        perms = perm_registry.get_permissions_for_scopes(['s1'])
        self.assertEqual(perms, {'p1'})

    def test_get_scopes_for_permission(self):
        perm_registry.register_permission('p1', 'P1', 'm')
        perm_registry.register_scope('s1', 'S1', ['p1'])

        scopes = perm_registry.get_scopes_for_permission('p1')
        self.assertEqual(scopes, ['s1'])

    def test_accessors(self):
        perm_registry.register_permission('p1', 'P1', 'm')
        perm_registry.register_role('r1', 'R1')
        perm_registry.register_scope('s1', 'S1', [])

        self.assertEqual(len(perm_registry.get_permission_list()), 1)
        self.assertEqual(len(perm_registry.get_permission_keys()), 1)
        self.assertEqual(len(perm_registry.get_role_list()), 1)
        self.assertEqual(len(perm_registry.get_scope_list()), 1)
        self.assertEqual(len(perm_registry.get_scope_keys()), 1)
