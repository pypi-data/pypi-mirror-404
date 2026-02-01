from unittest.mock import MagicMock

from django.contrib.auth.models import User
from django.contrib.sessions.backends.base import SessionBase
from django.test import RequestFactory, TestCase

from saas.sessions.middleware import SessionRecordMiddleware


class TestSessionRecordMiddleware(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser')
        self.get_response = MagicMock()
        self.middleware = SessionRecordMiddleware(self.get_response)

    def test_should_record_no_session(self):
        request = self.factory.get('/')
        # No session attribute
        self.assertFalse(self.middleware.should_record(request))

    def test_should_record_no_user(self):
        request = self.factory.get('/')
        request.session = MagicMock()
        # No user attribute
        self.assertFalse(self.middleware.should_record(request))

    def test_should_record_not_authenticated(self):
        request = self.factory.get('/')
        request.session = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(self.middleware.should_record(request))

    def test_should_record_no_user_id_in_session(self):
        request = self.factory.get('/')
        request.session = SessionBase()
        request.user = self.user
        self.assertFalse(self.middleware.should_record(request))

    def test_should_record_no_session_key(self):
        request = self.factory.get('/')
        request.session = MagicMock()
        request.session.get.return_value = self.user.id
        request.session.session_key = None
        request.user = self.user
        self.assertFalse(self.middleware.should_record(request))
