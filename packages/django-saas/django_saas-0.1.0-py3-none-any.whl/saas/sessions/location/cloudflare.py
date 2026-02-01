from saas.utils.ipware import get_client_ip

from .base import BaseBackend

CLIENT_IP_HEADERS = (
    'True-Client-IP',  # Header for CloudFlare Enterprise.
    'CF-Connecting-IP',  # Used by CloudFlare.
)


class CloudflareBackend(BaseBackend):
    # https://developers.cloudflare.com/rules/transform/managed-transforms/reference/#add-visitor-location-headers

    def resolve_ip(self, request):
        return get_client_ip(request, CLIENT_IP_HEADERS)

    def resolve_location(self, request):
        return dict(
            country=request.headers.get('CF-IPCountry'),
            region=request.headers.get('CF-Region'),
            region_code=request.headers.get('CF-Region-Code'),
        )
