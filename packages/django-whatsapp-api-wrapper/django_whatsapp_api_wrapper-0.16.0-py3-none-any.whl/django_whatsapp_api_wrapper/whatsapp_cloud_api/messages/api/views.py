from typing import Any, Dict

import requests
from rest_framework import status
from rest_framework.response import Response

from django.conf import settings

from ....authentication.base import BaseAuthenticatedAPIView

from .serializers import (
    MessageGenericSerializer,
    MessageTextSerializer,
    MessageTextReplySerializer,
    MessageTemplateSerializer,
    MessageButtonSerializer,
    MessageListSerializer,
)


def build_url() -> str:
    api_version = getattr(settings, "WHATSAPP_CLOUD_API_VERSION")
    phone_number_id = getattr(settings, "WHATSAPP_CLOUD_API_PHONE_NUMBER_ID")
    base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    return base_url


def auth_headers() -> Dict[str, str]:
    token = getattr(settings, "WHATSAPP_CLOUD_API_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


class MessageSendView(BaseAuthenticatedAPIView):
    def post(self, request):
        serializer = MessageGenericSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": data.get("recipient_type", "individual"),
            "to": data["to"],
            "type": data["type"],
        }
        if "context" in data:
            payload["context"] = data["context"]

        # Include the type-specific object
        payload[data["type"]] = data[data["type"]]

        resp = requests.post(build_url(), headers=auth_headers(), json=payload)
        body = resp.json() if resp.content else None
        return Response(body, status=resp.status_code)


class MessageTextView(BaseAuthenticatedAPIView):
    def post(self, request):
        serializer = MessageTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": v["to"],
            "type": "text",
            "text": {"preview_url": v.get("preview_url", False), "body": v["body"]},
        }
        resp = requests.post(build_url(), headers=auth_headers(), json=payload)
        return Response(resp.json() if resp.content else None, status=resp.status_code)


class MessageTextReplyView(BaseAuthenticatedAPIView):
    def post(self, request):
        serializer = MessageTextReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": v["to"],
            "context": {"message_id": v["reply_to"]},
            "type": "text",
            "text": {"preview_url": v.get("preview_url", False), "body": v["body"]},
        }
        resp = requests.post(build_url(), headers=auth_headers(), json=payload)
        return Response(resp.json() if resp.content else None, status=resp.status_code)


class MessageTemplateView(BaseAuthenticatedAPIView):
    def post(self, request):
        serializer = MessageTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": v["to"],
            "type": "template",
            "template": {
                "name": v["name"],
                "language": v["language"],
            },
        }
        if v.get("components"):
            payload["template"]["components"] = v["components"]

        resp = requests.post(build_url(), headers=auth_headers(), json=payload)
        return Response(resp.json() if resp.content else None, status=resp.status_code)


class MessageButtonView(BaseAuthenticatedAPIView):
    """
    POST /messages/buttons/
    Envia mensagem com botões de resposta rápida (máximo 3 botões).
    """

    def post(self, request):
        serializer = MessageButtonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        # Construir os botões no formato da API
        buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": btn["id"],
                    "title": btn["title"]
                }
            }
            for btn in v["buttons"]
        ]

        # Construir o objeto interactive
        interactive = {
            "type": "button",
            "body": {"text": v["body_text"]},
            "action": {"buttons": buttons}
        }

        if v.get("header_text"):
            interactive["header"] = {"type": "text", "text": v["header_text"]}
        if v.get("footer_text"):
            interactive["footer"] = {"text": v["footer_text"]}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": v["to"],
            "type": "interactive",
            "interactive": interactive
        }

        if v.get("context"):
            payload["context"] = v["context"]

        resp = requests.post(build_url(), headers=auth_headers(), json=payload)
        return Response(resp.json() if resp.content else None, status=resp.status_code)


class MessageListView(BaseAuthenticatedAPIView):
    """
    POST /messages/list/
    Envia mensagem com menu de lista.
    """

    def post(self, request):
        serializer = MessageListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        # Construir as seções no formato da API
        sections = [
            {
                "title": section.get("title"),
                "rows": [
                    {
                        "id": row["id"],
                        "title": row["title"],
                        **({"description": row["description"]} if row.get("description") else {})
                    }
                    for row in section["rows"]
                ]
            }
            for section in v["sections"]
        ]

        # Construir o objeto interactive
        interactive = {
            "type": "list",
            "body": {"text": v["body_text"]},
            "action": {
                "button": v["button_text"],
                "sections": sections
            }
        }

        if v.get("header_text"):
            interactive["header"] = {"type": "text", "text": v["header_text"]}
        if v.get("footer_text"):
            interactive["footer"] = {"text": v["footer_text"]}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": v["to"],
            "type": "interactive",
            "interactive": interactive
        }

        if v.get("context"):
            payload["context"] = v["context"]

        resp = requests.post(build_url(), headers=auth_headers(), json=payload)
        return Response(resp.json() if resp.content else None, status=resp.status_code)
