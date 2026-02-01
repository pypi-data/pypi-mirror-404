from django.urls import path

from .views import AcceptInvitationView

app_name = 'saas_identity'

urlpatterns = [
    path('invites/accept/<uuid:token>/', AcceptInvitationView.as_view(), name='invitation-accept'),
]
