import typing as t

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase

from saas.models import (
    Tenant,
    get_tenant_model,
)


class SaasTestCase(APITestCase):
    fixtures = [
        'test_data.yaml',
    ]

    client: APIClient
    client_class = APIClient

    tenant_id: int = 1
    user_id: int = 0

    SUPERUSER_USER_ID = 1
    STAFF_USER_ID = 2

    OWNER_USER_ID = 3
    ADMIN_USER_ID = 4
    MEMBER_USER_ID = 5
    GUEST_USER_ID = 6
    INACTIVE_USER_ID = 7

    def setUp(self) -> None:
        if self.tenant_id:
            self.client.credentials(
                HTTP_X_TENANT_ID=str(self.tenant_id),
            )

    @property
    def tenant(self):
        return self.get_tenant()

    @property
    def user(self):
        return self.get_user()

    def get_user(self, pk: t.Optional[int] = None) -> User:
        if pk is None:
            pk = self.user_id
        return get_user_model().objects.get(pk=pk)

    def get_tenant(self, pk: t.Optional[int] = None) -> Tenant:
        if pk is None:
            pk = self.tenant_id
        return get_tenant_model().objects.get(pk=pk)

    def force_login(self, user_id: int = None):
        if user_id is None:
            user = self.get_user()
        else:
            user = self.get_user(user_id)
        self.client.force_login(user)
        return user
