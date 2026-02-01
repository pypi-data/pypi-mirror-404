from unittest.mock import Mock

from django.test import override_settings
from rest_framework import serializers

from saas.drf.errors import BadRequest
from saas.drf.filters import (
    ChoiceFilter,
    CurrentUserFilter,
    IncludeFilter,
    TenantIdFilter,
)
from saas.settings import saas_settings
from saas.test import SaasTestCase


class TestFilters(SaasTestCase):
    def test_current_user_filter(self):
        request = Mock()
        request.user = Mock()
        queryset = Mock()

        f = CurrentUserFilter()
        f.filter_queryset(request, queryset, None)
        queryset.filter.assert_called_with(user=request.user)

    def test_tenant_id_filter_no_tenant(self):
        request = Mock()
        request.tenant_id = None
        f = TenantIdFilter()
        with self.assertRaises(BadRequest):
            f.filter_queryset(request, Mock(), Mock())

    def test_tenant_id_filter_success(self):
        request = Mock()
        request.tenant_id = '123'
        queryset = Mock()
        view = Mock()
        # default tenant_id_field is tenant_id
        view.tenant_id_field = 'tenant_id'

        f = TenantIdFilter()
        f.filter_queryset(request, queryset, view)
        queryset.filter.assert_called_with(tenant_id='123')

    @override_settings(MIDDLEWARE=['saas.middleware.HeaderTenantIdMiddleware'])
    def test_tenant_id_schema_header(self):
        f = TenantIdFilter()
        params = f.get_schema_operation_parameters(Mock())
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]['in'], 'header')
        self.assertEqual(params[0]['name'], saas_settings.TENANT_ID_HEADER)
        self.assertTrue(params[0]['required'])

    @override_settings(MIDDLEWARE=['saas.middleware.PathTenantIdMiddleware'])
    def test_tenant_id_schema_path(self):
        f = TenantIdFilter()
        params = f.get_schema_operation_parameters(Mock())
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]['in'], 'path')
        self.assertTrue(params[0]['required'])

    @override_settings(
        MIDDLEWARE=['saas.middleware.HeaderTenantIdMiddleware', 'saas.middleware.PathTenantIdMiddleware']
    )
    def test_tenant_id_schema_both(self):
        f = TenantIdFilter()
        params = f.get_schema_operation_parameters(Mock())
        self.assertEqual(len(params), 2)
        # Both should be optional if both are present
        self.assertFalse(params[0]['required'])
        self.assertFalse(params[1]['required'])

    def test_include_filter_no_fields(self):
        request = Mock()
        view = Mock()
        view.include_select_related_fields = []
        view.include_prefetch_related_fields = []
        view.include_annotate_fields = []

        f = IncludeFilter()
        qs = Mock()
        self.assertEqual(f.filter_queryset(request, qs, view), qs)

    def test_include_filter_select_related(self):
        request = Mock()
        request.query_params = {'include': 'rel1'}
        view = Mock()
        view.include_select_related_fields = ['rel1']
        view.include_prefetch_related_fields = []
        view.include_annotate_fields = []

        f = IncludeFilter()
        qs = Mock()
        f.filter_queryset(request, qs, view)
        qs.select_related.assert_called_with('rel1')

    def test_include_filter_prefetch_related(self):
        request = Mock()
        request.query_params = {'include': 'rel2'}
        view = Mock()
        view.include_select_related_fields = []
        view.include_prefetch_related_fields = ['rel2', 'rel2__child']
        view.include_annotate_fields = []

        f = IncludeFilter()
        qs = Mock()
        qs.prefetch_related.return_value = qs
        f.filter_queryset(request, qs, view)

        # Check that prefetch_related was called for rel2
        # And potentially for rel2__child if logic does so
        qs.prefetch_related.assert_any_call('rel2')
        qs.prefetch_related.assert_any_call('rel2__child')

    def test_include_filter_annotate(self):
        request = Mock()
        request.query_params = {'include': 'anno1'}
        view = Mock()
        view.include_select_related_fields = []
        view.include_prefetch_related_fields = []
        view.include_annotate_fields = ['anno1']
        view.annotate_queryset = Mock(return_value='annotated_qs')

        f = IncludeFilter()
        qs = Mock()
        res = f.filter_queryset(request, qs, view)
        view.annotate_queryset.assert_called_with(qs, ['anno1'])
        self.assertEqual(res, 'annotated_qs')

    def test_include_filter_all(self):
        request = Mock()
        request.query_params = {'include': 'all'}
        view = Mock()
        view.include_select_related_fields = ['rel1']
        view.include_prefetch_related_fields = []
        view.include_annotate_fields = []

        f = IncludeFilter()
        qs = Mock()
        f.filter_queryset(request, qs, view)
        qs.select_related.assert_called_with('rel1')

    def test_include_filter_schema(self):
        view = Mock()
        view.include_select_related_fields = ['rel1']
        view.include_prefetch_related_fields = ['rel2']
        view.include_annotate_fields = []

        f = IncludeFilter()
        params = f.get_schema_operation_parameters(view)
        self.assertEqual(len(params), 1)
        self.assertIn('rel1', params[0]['description'])
        self.assertIn('rel2', params[0]['description'])

    def test_choice_filter(self):
        class S(serializers.Serializer):
            status = serializers.ChoiceField(choices=['active', 'inactive'])

        view = Mock()
        view.choice_filter_fields = ['status']
        view.get_serializer_class.return_value = S

        request = Mock()
        request.query_params = {'status': 'active'}

        f = ChoiceFilter()
        qs = Mock()
        f.filter_queryset(request, qs, view)
        qs.filter.assert_called_with(status='active')

    def test_choice_filter_invalid_value(self):
        class S(serializers.Serializer):
            count = serializers.IntegerField()

        view = Mock()
        view.choice_filter_fields = ['count']
        view.get_serializer_class.return_value = S

        request = Mock()
        request.query_params = {'count': 'not-an-int'}

        f = ChoiceFilter()
        qs = Mock()
        # Should continue without filtering
        f.filter_queryset(request, qs, view)
        qs.filter.assert_not_called()

    def test_choice_filter_schema(self):
        class S(serializers.Serializer):
            status = serializers.ChoiceField(choices=['active', 'inactive'])
            flag = serializers.BooleanField()

        view = Mock()
        view.choice_filter_fields = ['status', 'flag']
        view.get_serializer_class.return_value = S

        f = ChoiceFilter()
        schema = f.get_schema_operation_parameters(view)
        self.assertEqual(len(schema), 2)

        status_schema = next(s for s in schema if s['name'] == 'status')
        self.assertIn('active', status_schema['schema']['enum'])

        flag_schema = next(s for s in schema if s['name'] == 'flag')
        self.assertEqual(flag_schema['schema']['type'], 'boolean')
