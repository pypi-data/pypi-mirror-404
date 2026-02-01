from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema


class FixedUserTokenListEndpoint(OpenApiViewExtension):
    target_class = 'saas.tokens.endpoints.UserTokenListEndpoint'

    def view_replacement(self):
        class UserTokenListEndpoint(self.target_class):
            @extend_schema(tags=['Token'], summary='List user tokens')
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Token'], summary='Create a user token')
            def post(self, *args, **kwargs):
                pass

        return UserTokenListEndpoint


class FixedUserTokenItemEndpoint(OpenApiViewExtension):
    target_class = 'saas.tokens.endpoints.UserTokenItemEndpoint'

    def view_replacement(self):
        class UserTokenItemEndpoint(self.target_class):
            @extend_schema(tags=['Token'], summary='Delete a user token')
            def delete(self, *args, **kwargs):
                pass

        return UserTokenItemEndpoint
