from django.urls import path

from .endpoints import SessionRecordItemEndpoint, SessionRecordListEndpoint

urlpatterns = [
    path('', SessionRecordListEndpoint.as_view()),
    path('<uuid:pk>/', SessionRecordItemEndpoint.as_view()),
]
