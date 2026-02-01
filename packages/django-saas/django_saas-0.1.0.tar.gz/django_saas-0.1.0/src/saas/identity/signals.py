from django.dispatch import Signal

after_signup_user = Signal()
after_login_user = Signal()
invitation_created = Signal()
invitation_accepted = Signal()
member_invited = Signal()
