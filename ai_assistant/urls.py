from django.urls import path
from . import views

app_name = "ai_assistant"

urlpatterns = [
    path("", views.assistant_panel, name="panel"),
    path("chat/", views.assistant_chat, name="chat"),
    path("conversation/<int:pk>/", views.conversation_messages, name="conversation_messages"),
    path("field-help/", views.field_help, name="field_help"),
    path("action/confirm/", views.confirm_action, name="confirm_action"),
]
