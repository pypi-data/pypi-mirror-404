from django.conf import settings
from django.http import Http404
from django.views.generic import RedirectView

from saas.identity.settings import identity_settings

from .models import Invitation, UserEmail

__all__ = [
    'AcceptInvitationView',
]


class AcceptInvitationView(RedirectView):
    def get_invitation_redirect_url(self, invitation: Invitation):
        if UserEmail.objects.filter(email=invitation.email).exists():
            login_url = identity_settings.LOGIN_URL or settings.LOGIN_URL
            return login_url + '?invite_code=' + str(invitation.token)
        else:
            return identity_settings.SIGNUP_URL + '?invite_code=' + str(invitation.token)

    def get_redirect_url(self, *args, **kwargs):
        try:
            invitation = Invitation.objects.get(**kwargs)
        except Invitation.DoesNotExist:
            raise Http404()

        if invitation.is_expired():
            raise Http404('Invitation has expired.')

        if invitation.status == Invitation.InviteStatus.SENT:
            return self.get_invitation_redirect_url(invitation)
        elif invitation.status == Invitation.InviteStatus.ACCEPTED:
            login_url = identity_settings.LOGIN_URL or settings.LOGIN_URL
            return login_url
        raise Http404()
