from django.urls import path

from .endpoints.groups import GroupItemEndpoint, GroupListEndpoint
from .endpoints.members import (
    MemberItemEndpoint,
    MemberListEndpoint,
)

group_urls = [
    path('', GroupListEndpoint.as_view()),
    path('<pk>/', GroupItemEndpoint.as_view()),
]

member_urls = [
    path('', MemberListEndpoint.as_view()),
    path('<pk>/', MemberItemEndpoint.as_view()),
]
