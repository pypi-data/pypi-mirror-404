import typing as t
from collections import OrderedDict, defaultdict

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from rest_framework.fields import ChoiceField as _ChoiceField
from rest_framework.fields import Field
from rest_framework.serializers import ModelSerializer as _ModelSerializer
from rest_framework.serializers import Serializer
from rest_framework.validators import ValidationError

__all__ = [
    'ChoiceField',
    'RelatedSerializerField',
    'ModelSerializer',
    'FlattenModelSerializer',
]


class ChoiceField(_ChoiceField):
    """Rewrite this fields to support (int, str) choices."""

    def __init__(self, choices, **kwargs):
        super().__init__(choices, **kwargs)

        self.int_str_choices: t.Dict[int, str] = {}
        self.str_int_choices: t.Dict[str, int] = {}
        if choices:
            self._set_int_str_choices(choices)

    def _set_int_str_choices(self, choices: t.List[t.Tuple[int, str]]):
        int_str_choices: t.Dict[int, str] = {}
        str_int_choices: t.Dict[str, int] = {}
        for choice in choices:
            if len(choice) == 2 and isinstance(choice[0], int):
                int_str_choices[choice[0]] = choice[1]
                str_int_choices[choice[1]] = choice[0]
            else:
                return
        self.int_str_choices = int_str_choices
        self.str_int_choices = str_int_choices

    def to_internal_value(self, data):
        if data == '' and self.allow_blank:
            return ''

        if self.str_int_choices:
            try:
                return self.str_int_choices[str(data)]
            except KeyError:
                self.fail('invalid_choice', input=data)

        try:
            return self.choice_strings_to_values[str(data)]
        except KeyError:
            self.fail('invalid_choice', input=data)

    def to_representation(self, value):
        if value in ('', None):
            return value

        if self.int_str_choices:
            return self.int_str_choices[value]

        return self.choice_strings_to_values.get(str(value), value)


class RelatedSerializerField(Field):
    def __init__(self, serializer_cls, **kwargs):
        self.serializer_cls = serializer_cls
        self.many = kwargs.pop('many', False)
        super().__init__(**kwargs)

    def to_representation(self, value: QuerySet):
        return self.serializer_cls(value, many=self.many).data

    def to_internal_value(self, data):
        model = self.serializer_cls.Meta.model
        if self.many and not isinstance(data, list):
            raise ValidationError(f'Expected a list of {model.__name__} IDs.')

        if self.many:
            return model.objects.filter(pk__in=data)
        try:
            return model.objects.get(pk=data)
        except model.DoesNotExist:
            raise ValidationError(f'Invalid {model.__name__} ID.')


class ModelSerializer(_ModelSerializer):
    serializer_choice_field = ChoiceField

    @property
    def _readable_fields(self):
        request_include_fields = getattr(self.Meta, 'request_include_fields', [])
        if not request_include_fields:
            for field in self.fields.values():
                if not field.write_only:
                    yield field
        else:
            include_terms = self.context.get('include_fields', [])
            if not include_terms:
                request = self.context.get('request')
                if request:
                    include_terms = getattr(request, 'include_terms', [])

            for field in self.fields.values():
                if field.field_name in request_include_fields and field.field_name not in include_terms:
                    continue

                if not field.write_only:
                    yield field


class FlattenModelSerializer(ModelSerializer):
    @property
    def _flatten_fields(self) -> t.List[str]:
        return getattr(self.Meta, 'flatten_fields', [])

    def get_fields(self):
        fields = super().get_fields()
        if not self._flatten_fields:
            return fields

        new_fields = OrderedDict()
        for root_name, field in fields.items():
            if root_name in self._flatten_fields and isinstance(field, Serializer):
                field.field_name = root_name
                nested_fields = field.get_fields()
                for nested_name, nested_field in nested_fields.items():
                    nested_field._flatten_parent = field
                    if nested_field.source:
                        nested_field.source = f'{root_name}.{nested_field.source}'
                    else:
                        nested_field.source = f'{root_name}.{nested_name}'

                    # Handle naming collisions: if field exists in root, prefix it
                    if nested_name in fields:
                        new_fields[f'{root_name}_{nested_name}'] = nested_field
                    else:
                        new_fields[nested_name] = nested_field
            else:
                new_fields[root_name] = field
        return new_fields

    def to_internal_value(self, data):
        if not self._flatten_fields:
            return super().to_internal_value(data)

        internal_data = data.copy()
        nested_data = defaultdict(dict)
        nested_serializers = {}
        for field_name, field in self.fields.items():
            if hasattr(field, '_flatten_parent'):
                parent_field = getattr(field, '_flatten_parent')
                root_name = parent_field.field_name
                nested_serializers[root_name] = parent_field
                nested_key = f'{root_name}_{field_name}'
                if nested_key in internal_data:
                    nested_data[root_name][field_name] = internal_data.pop(nested_key)
                elif field_name in internal_data:
                    nested_data[root_name][field_name] = internal_data.pop(field_name)

        result = super().to_internal_value(internal_data)

        # Validate nested fields
        for root_name, nested_data in nested_data.items():
            serializer = nested_serializers[root_name]
            validated_data = serializer.to_internal_value(nested_data)
            result[root_name] = validated_data
        return result

    @staticmethod
    def _get_related_field_name(instance, model):
        for field in model._meta.get_fields():
            # Check if this field is a relation pointing to our parent model
            if field.is_relation and field.related_model == instance.__class__:
                return field.name

        # Fallback or Raise error if no relation is found
        raise AttributeError(f'No relation from {model.__name__} back to {instance.__class__.__name__}.')

    def _update_nested_fields(self, instance, data: t.Dict[str, t.Any]):
        nested_serializers = {}
        for field in self.fields.values():
            if hasattr(field, '_flatten_parent'):
                parent_field = getattr(field, '_flatten_parent')
                nested_serializers[parent_field.field_name] = parent_field

        for name, value in data.items():
            serializer_field = nested_serializers[name]
            try:
                related_instance = getattr(instance, name)
                serializer_field.update(related_instance, value)
            except (ObjectDoesNotExist, AttributeError):
                nested_model = serializer_field.Meta.model
                instance_name = self._get_related_field_name(instance, nested_model)
                value[instance_name] = instance
                serializer_field.create(value)

    def create(self, validated_data):
        nested_data = {f: validated_data.pop(f) for f in self._flatten_fields if f in validated_data}
        obj = super().create(validated_data)
        self._update_nested_fields(obj, nested_data)
        return obj

    def update(self, instance, validated_data):
        nested_data = {f: validated_data.pop(f) for f in self._flatten_fields if f in validated_data}
        obj = super().update(instance, validated_data)
        self._update_nested_fields(obj, nested_data)
        return obj
