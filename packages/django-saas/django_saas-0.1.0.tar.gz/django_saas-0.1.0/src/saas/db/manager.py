import hashlib
import logging
import typing as t
import uuid

from django.db.models import Manager, Model, QuerySet, UUIDField
from django.db.models.signals import (
    class_prepared,
    m2m_changed,
    post_delete,
    post_save,
)

from .cache import cache

__all__ = ['CachedManager']

logger = logging.getLogger(__name__)

M = t.TypeVar('M', bound=Model)


class CachedManager(Manager, t.Generic[M]):
    db_cache = cache
    natural_key: list[str] = []
    cache_ttl: int = 300
    cache_version = 2
    query_select_related: list[str] = []
    query_prefetch_related: list[str] = []

    def contribute_to_class(self, model: t.Type[M], name: str):
        super().contribute_to_class(model, name)
        class_prepared.connect(self.__manage_cache, sender=model)

    def _filter_related_queryset(self, queryset: QuerySet[M]) -> QuerySet[M]:
        if self.query_select_related:
            queryset = queryset.select_related(*self.query_select_related)
        if self.query_prefetch_related:
            queryset = queryset.prefetch_related(*self.query_prefetch_related)
        return queryset

    def get_many_from_cache(self, pk_set: list[t.Any]) -> dict[t.Any, M]:
        key_map = {self.__get_lookup_cache_key(pk=pk): pk for pk in pk_set}
        results = self.db_cache.get_many(key_map.keys(), version=self.cache_version)

        found = {}
        missed = []
        for key in key_map:
            if key not in results:
                missed.append(key_map[key])
            else:
                found[key_map[key]] = results[key]

        if missed:
            queryset = self._filter_related_queryset(self.filter(pk__in=missed))
            to_delete = []
            to_save = {}
            to_recover = []
            for instance in queryset:
                resolved = self.__resolve_instance_caches(instance, False)
                to_delete.extend(resolved['delete'])
                to_save.update(resolved['save'])
                to_recover.append(resolved['recover_state'])

            if to_delete:
                self.db_cache.delete_many(to_delete, version=self.cache_version)
            if to_save:
                self.db_cache.set_many(to_save, timeout=self.cache_ttl, version=self.cache_version)

            for instance, db in to_recover:
                instance._state.db = db
                found[instance.pk] = instance
        return found

    def get_from_cache_by_pk(self, pk: t.Any) -> M:
        key = self.__get_lookup_cache_key(pk=pk)
        instance = self.__get_from_cache_or_raise(key)
        if instance:
            instance._state.db = self.db
            return instance

        try:
            instance: M = self._filter_related_queryset(self).get(pk=pk)
        except self.model.DoesNotExist:
            self.__set_not_exist_cache(key)
            raise self.model.DoesNotExist

        self.__save_db_cache(instance)
        return instance

    def get_from_cache_by_natural_key(self, *args) -> M:
        kwargs = dict(zip(self.natural_key, args))
        key = self.__get_lookup_cache_key(**kwargs)
        pk_val = self.__get_from_cache_or_raise(key)
        if pk_val:
            return self.get_from_cache_by_pk(pk_val)

        try:
            instance = self._filter_related_queryset(self).get(**kwargs)
        except self.model.DoesNotExist:
            self.__set_not_exist_cache(key)
            raise self.model.DoesNotExist

        self.__save_db_cache(instance)
        return instance

    def purge(self, pk_value):
        key = self.__get_lookup_cache_key(pk=pk_value)
        self.db_cache.delete(key, version=self.cache_version)

    def purge_many(self, pk_values):
        keys = [self.__get_lookup_cache_key(pk=pk) for pk in pk_values]
        self.db_cache.delete_many(keys, version=self.cache_version)

    def __manage_cache(self, sender, **kwargs):
        uid = f'{sender._meta.label}.cached_manager'
        post_save.connect(self.__post_save, sender=sender, weak=False, dispatch_uid=f'{uid}_save')
        post_delete.connect(self.__post_delete, sender=sender, weak=False, dispatch_uid=f'{uid}_delete')

    def setup_related_cache_invalidation(self):
        main_model = self.model
        for field_name in self.query_select_related:
            field = main_model._meta.get_field(field_name)
            self.__invalidate_related_cache(main_model, field.related_model, field_name)

        for field_name in self.query_prefetch_related:
            field = main_model._meta.get_field(field_name)
            self.__invalidate_related_cache(main_model, field.related_model, field_name)
            if field.many_to_many:
                self.__invalidate_m2m_cache(main_model, field)

    def __invalidate_related_cache(self, main_model, related_model, filter_key):
        def _handler(sender, instance, **kwargs):
            pk_values = main_model.objects.filter(**{filter_key: instance}).values_list('pk', flat=True)
            self.purge_many(pk_values)

        dispatch_uid = f'{main_model._meta.label}__{related_model._meta.label}.cached_manager'
        post_save.connect(_handler, sender=related_model, weak=False, dispatch_uid=f'{dispatch_uid}_save')
        post_delete.connect(_handler, sender=related_model, weak=False, dispatch_uid=f'{dispatch_uid}_delete')

    def __invalidate_m2m_cache(self, main_model, field):
        filter_key = field.remote_field.name

        def m2m_handler(sender, instance, action, **kwargs):
            if action in ['post_add', 'post_remove', 'post_clear']:
                if isinstance(instance, main_model):
                    self.purge(instance.pk)
                else:
                    pk_values = main_model.objects.filter(**{filter_key: instance}).values_list('pk', flat=True)
                    self.purge_many(pk_values)

        m2m_changed.connect(m2m_handler, sender=field.remote_field.through, weak=False)

    def __get_from_cache_or_raise(self, key: str):
        value = self.db_cache.get(key, version=self.cache_version)
        if value == '__none__':
            raise self.model.DoesNotExist
        return value

    def __set_not_exist_cache(self, key: str):
        self.db_cache.set(
            key=key,
            value='__none__',
            timeout=self.cache_ttl,
            version=self.cache_version,
        )

    def __get_lookup_cache_key(self, **kwargs) -> str:
        key = make_key(self.model, kwargs)
        return f'db:{self.model._meta.db_table}:{key}'

    def __get_natural_cache_key(self, instance: M) -> str:
        natural_fields = {key: value_for_field(instance, key) for key in self.natural_key}
        return self.__get_lookup_cache_key(**natural_fields)

    def __post_save(self, instance, **kwargs):
        self.__save_db_cache(instance, **kwargs)
        # transaction.on_commit(lambda: self.__save_db_cache(instance, **kwargs))

    def __resolve_instance_caches(self, instance, created: bool):
        if not created:
            _natural_cache_key = self.db_cache.get(
                self.__get_lookup_cache_key(__track=instance.pk),
                version=self.cache_version,
            )
        else:
            _natural_cache_key = None

        to_delete = []
        natural_cache_key = self.__get_natural_cache_key(instance)
        if _natural_cache_key and _natural_cache_key != natural_cache_key:
            to_delete.append(_natural_cache_key)

        # natural key and pk mapping
        to_save = {
            natural_cache_key: instance.pk,
            self.__get_lookup_cache_key(__track=instance.pk): natural_cache_key,
        }

        # Ensure we don't serialize the database into the cache
        db = instance._state.db
        instance._state.db = None

        instance_key = self.__get_lookup_cache_key(pk=instance.pk)
        to_save[instance_key] = instance
        return {'save': to_save, 'delete': to_delete, 'recover_state': (instance, db)}

    def __save_db_cache(self, instance, **kwargs):
        resolved = self.__resolve_instance_caches(instance, kwargs.get('created', False))

        to_delete = resolved['delete']
        if to_delete:
            self.db_cache.delete_many(to_delete, version=self.cache_version)

        to_save = resolved['save']
        if to_save:
            self.db_cache.set_many(to_save, timeout=self.cache_ttl, version=self.cache_version)

        # recover database on instance
        resolved['recover_state'][0]._state.db = resolved['recover_state'][1]

    def __post_delete(self, instance, **kwargs):
        to_delete = [
            self.__get_lookup_cache_key(pk=instance.pk),
            self.__get_natural_cache_key(instance),
            self.__get_lookup_cache_key(__track=instance.pk),
        ]
        self.db_cache.delete_many(to_delete, version=self.cache_version)


def make_key(cls: Model, kwargs: t.Mapping[str, t.Union[Model, int, str]]) -> str:
    fields = []
    for k, v in sorted(kwargs.items()):
        if k == 'pk':
            # convert pk to its real name
            k = str(cls._meta.pk.name)
            if isinstance(v, str) and isinstance(cls._meta.pk, UUIDField):
                v = v.replace('-', '')
        if isinstance(v, Model):
            v = v.pk
        if isinstance(v, uuid.UUID):
            v = v.hex
        fields.append(f'{k}={v}')
    return hashlib.md5('&'.join(fields).encode('utf-8')).hexdigest()


def value_for_field(instance: M, key: str) -> t.Any:
    field = instance._meta.get_field(key)
    return getattr(instance, field.attname)
