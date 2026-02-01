from __future__ import annotations

import fnmatch


def has_permission(required_perm: str, assigned_perms: set[str]):
    if not assigned_perms:
        return False

    if required_perm in assigned_perms or '*' in assigned_perms:
        return True

    glob_patterns = [p for p in assigned_perms if '*' in p]
    for pattern in glob_patterns:
        if fnmatch.fnmatchcase(required_perm, pattern):
            return True
    return False


def get_view_permission(view, method) -> str | None:
    handler = getattr(view, method.lower(), None)
    if handler:
        perm = getattr(handler, '_required_permission', None)
        if perm:
            return perm

    perm_func = getattr(view, 'get_required_permission', None)
    if perm_func:
        return perm_func()

    perm = getattr(view, 'required_permission', None)
    if perm is None:
        return None

    if perm.count('.') == 1:
        method_actions = {
            'HEAD': 'view',
            'GET': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        return f'{perm}.{method_actions[method]}'
    return perm
