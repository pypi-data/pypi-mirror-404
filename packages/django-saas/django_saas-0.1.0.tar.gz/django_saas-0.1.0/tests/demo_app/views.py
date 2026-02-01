from rest_framework.response import Response

from saas.drf.views import TenantEndpoint

from .models import TenantSecret


class TenantSecretListEndpoint(TenantEndpoint):
    queryset = TenantSecret.objects.all()
    required_permission = 'org.secret'

    def post(self, request, *args, **kwargs):
        secret: str = request.data['secret']
        obj = TenantSecret.objects.create(tenant_id=self.get_tenant_id())
        obj.secret = secret.encode('utf-8')
        obj.save()
        data = {'id': obj.id}
        return Response(data, status=201)


class TenantSecretItemEndpoint(TenantEndpoint):
    queryset = TenantSecret.objects.all()
    required_permission = 'org.secret'

    def get_required_permission(self):
        if self.request.method == 'GET':
            return 'org.secret.view'
        else:
            return 'org.secret.update'

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return Response({'secret': obj.secret})

    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        secret: str = request.data['secret']
        obj.secret = secret.encode('utf-8')
        obj.save()
        return Response(status=204)
