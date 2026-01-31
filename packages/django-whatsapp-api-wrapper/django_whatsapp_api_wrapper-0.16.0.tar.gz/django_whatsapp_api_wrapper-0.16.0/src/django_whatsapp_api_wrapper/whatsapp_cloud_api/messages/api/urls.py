from django.urls import path

from .views import (
    MessageSendView,
    MessageTextReplyView,
    MessageTextView,
    MessageTemplateView,
    MessageButtonView,
    MessageListView,
)


urlpatterns = [
    path("send/", MessageSendView.as_view(), name="wa_messages_send"),
    path("text/", MessageTextView.as_view(), name="wa_messages_text"),
    path("text/reply/", MessageTextReplyView.as_view(), name="wa_messages_text_reply"),
    path("template/", MessageTemplateView.as_view(), name="wa_messages_template"),
    path("buttons/", MessageButtonView.as_view(), name="wa_messages_buttons"),
    path("list/", MessageListView.as_view(), name="wa_messages_list"),
]


