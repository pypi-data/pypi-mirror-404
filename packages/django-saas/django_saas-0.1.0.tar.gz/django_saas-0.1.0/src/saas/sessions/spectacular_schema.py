from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema


class FixedSessionRecordListEndpoint(OpenApiViewExtension):
    target_class = 'saas.sessions.endpoints.SessionRecordListEndpoint'

    def view_replacement(self):
        class SessionRecordListEndpoint(self.target_class):
            @extend_schema(tags=['Session'], summary='List user sessions')
            def get(self, *args, **kwargs):
                pass

        return SessionRecordListEndpoint


class FixedSessionRecordItemEndpoint(OpenApiViewExtension):
    target_class = 'saas.sessions.endpoints.SessionRecordItemEndpoint'

    def view_replacement(self):
        class SessionRecordItemEndpoint(self.target_class):
            @extend_schema(tags=['Session'], summary='Retrieve a user session')
            def get(self, *args, **kwargs):
                pass

            @extend_schema(tags=['Session'], summary='Delete a user session')
            def delete(self, *args, **kwargs):
                pass

        return SessionRecordItemEndpoint
