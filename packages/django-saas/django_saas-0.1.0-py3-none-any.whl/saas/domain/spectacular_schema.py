from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema

from .serializers import DomainSetPrimarySerializer


class FixedDomainListEndpoint(OpenApiViewExtension):
    target_class = 'saas.domain.endpoints.domain.DomainListEndpoint'

    def view_replacement(self):
        class DomainListEndpoint(self.target_class):
            @extend_schema(tags=['Domain'], summary='List Domains')
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Domain'], summary='Add Domain')
            def post(self, *args, **kwargs):
                pass

        return DomainListEndpoint


class FixedDomainItemEndpoint(OpenApiViewExtension):
    target_class = 'saas.domain.endpoints.domain.DomainItemEndpoint'

    def view_replacement(self):
        class DomainItemEndpoint(self.target_class):
            @extend_schema(tags=['Domain'], summary='Retrieve Domain')
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Domain'], summary='Re-add Domain', request=None)
            def post(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Domain'], summary='Set Primary Domain', request=DomainSetPrimarySerializer)
            def patch(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Domain'], summary='Remove Domain')
            def delete(self, *args, **kwargs):
                pass

        return DomainItemEndpoint


class FixedDomainVerifyEndpoint(OpenApiViewExtension):
    target_class = 'saas.domain.endpoints.domain.DomainVerifyEndpoint'

    def view_replacement(self):
        class DomainVerifyEndpoint(self.target_class):
            @extend_schema(tags=['Domain'], summary='Verify Domain', request=None)
            def post(self, *args, **kwargs):
                pass

        return DomainVerifyEndpoint
