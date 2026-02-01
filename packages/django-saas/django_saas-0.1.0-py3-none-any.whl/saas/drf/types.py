from __future__ import annotations

import typing as t

from rest_framework.request import Request

if t.TYPE_CHECKING:
    from saas.models import Tenant
    from saas.tenancy.models import Member


class SaasRequest(Request):
    tenant: 'Tenant'
    tenant_member: 'Member'
    tenant_id: t.Any
