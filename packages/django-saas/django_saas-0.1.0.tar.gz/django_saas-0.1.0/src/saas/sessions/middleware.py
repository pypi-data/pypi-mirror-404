from django.contrib.auth import SESSION_KEY as USER_SESSION_KEY
from django.utils import timezone

from saas.sessions.models import Session
from saas.sessions.settings import session_settings

__all__ = ['SessionRecordMiddleware']

LAST_RECORD_KEY = '_last_record_time'


class SessionRecordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def should_record(self, request):
        if not hasattr(request, 'session'):
            return False

        if not hasattr(request, 'user'):
            return False

        if not request.user.is_authenticated:
            return False

        user_id = request.session.get(USER_SESSION_KEY)
        if not user_id:
            return False

        if not request.session.session_key:
            return False

        last_record = request.session.get(LAST_RECORD_KEY)
        if not last_record:
            return True

        now = timezone.now().timestamp()
        return now - last_record > session_settings.SESSION_RECORD_INTERVAL

    def record_session(self, request):
        user_id = request.session.get(USER_SESSION_KEY)
        session_key = request.session.session_key
        expiry_date = request.session.get_expiry_date()
        user_agent = request.headers.get('User-Agent', '')
        location = session_settings.LOCATION_RESOLVER.resolve(request)
        Session.objects.update_or_create(
            user_id=user_id,
            session_key=session_key,
            defaults={
                'expiry_date': expiry_date,
                'user_agent': user_agent,
                'location': location,
                'last_used': timezone.now(),
            },
        )

    def __call__(self, request):
        if self.should_record(request):
            self.record_session(request)
            now = timezone.now().timestamp()
            request.session[LAST_RECORD_KEY] = int(now)

        return self.get_response(request)
