from django.contrib.gis.geoip2 import GeoIP2, GeoIP2Exception

from saas.utils.ipware import get_client_ip

from .base import BaseBackend

_geo = GeoIP2()


class GeoIP2Backend(BaseBackend):
    def resolve_ip(self, request):
        return get_client_ip(request)

    def resolve_location(self, request):
        ip = get_client_ip(request)
        if ip is None:
            return {}

        try:
            info = _geo.city(ip)
            return dict(
                ip=ip,
                country=info.get('country_code'),
                region=info.get('region_name'),
                region_code=info.get('region_code'),
            )
        except GeoIP2Exception:
            return {}
