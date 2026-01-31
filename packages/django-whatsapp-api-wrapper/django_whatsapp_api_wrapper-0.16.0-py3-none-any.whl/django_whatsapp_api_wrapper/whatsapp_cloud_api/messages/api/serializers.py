from typing import Any, Dict, Optional

from rest_framework import serializers


class MessageGenericSerializer(serializers.Serializer):
    to = serializers.CharField()
    recipient_type = serializers.ChoiceField(choices=[("individual", "individual")], required=False)
    type = serializers.ChoiceField(
        choices=[
            ("text", "text"),
            ("template", "template"),
            ("image", "image"),
            ("audio", "audio"),
            ("document", "document"),
            ("video", "video"),
            ("sticker", "sticker"),
            ("location", "location"),
            ("contacts", "contacts"),
            ("reaction", "reaction"),
            ("interactive", "interactive"),
        ]
    )

    # Optional common fields
    context = serializers.DictField(required=False)

    # Payloads per type (passed through to the Graph API)
    text = serializers.DictField(required=False)
    template = serializers.DictField(required=False)
    image = serializers.DictField(required=False)
    audio = serializers.DictField(required=False)
    document = serializers.DictField(required=False)
    video = serializers.DictField(required=False)
    sticker = serializers.DictField(required=False)
    location = serializers.DictField(required=False)
    contacts = serializers.DictField(required=False)
    reaction = serializers.DictField(required=False)
    interactive = serializers.DictField(required=False)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        message_type: str = attrs.get("type")
        payload = attrs.get(message_type)
        if payload is None:
            raise serializers.ValidationError({message_type: "is required for this message type"})
        return attrs


class MessageTextSerializer(serializers.Serializer):
    to = serializers.CharField()
    body = serializers.CharField()
    preview_url = serializers.BooleanField(required=False, default=False)


class MessageTextReplySerializer(serializers.Serializer):
    to = serializers.CharField()
    reply_to = serializers.CharField()
    body = serializers.CharField()
    preview_url = serializers.BooleanField(required=False, default=False)


class MessageTemplateSerializer(serializers.Serializer):
    to = serializers.CharField()
    name = serializers.CharField()
    language = serializers.DictField()
    components = serializers.ListField(child=serializers.DictField(), required=False)


class ButtonSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=256)
    title = serializers.CharField(max_length=20)


class MessageButtonSerializer(serializers.Serializer):
    """Serializer para mensagens com botões de resposta rápida (máx 3 botões)"""
    to = serializers.CharField()
    body_text = serializers.CharField(max_length=1024)
    buttons = serializers.ListField(
        child=ButtonSerializer(),
        min_length=1,
        max_length=3,
        help_text="Lista de botões (máx 3). Cada botão: {id, title}"
    )
    header_text = serializers.CharField(max_length=60, required=False)
    footer_text = serializers.CharField(max_length=60, required=False)
    context = serializers.DictField(required=False, help_text="Para responder a uma mensagem específica")


class SectionRowSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=200)
    title = serializers.CharField(max_length=24)
    description = serializers.CharField(max_length=72, required=False)


class SectionSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=24, required=False)
    rows = serializers.ListField(
        child=SectionRowSerializer(),
        min_length=1,
        max_length=10
    )


class MessageListSerializer(serializers.Serializer):
    """Serializer para mensagens com menu de lista"""
    to = serializers.CharField()
    body_text = serializers.CharField(max_length=1024)
    button_text = serializers.CharField(max_length=20, help_text="Texto do botão que abre o menu")
    sections = serializers.ListField(
        child=SectionSerializer(),
        min_length=1,
        max_length=10,
        help_text="Lista de seções do menu"
    )
    header_text = serializers.CharField(max_length=60, required=False)
    footer_text = serializers.CharField(max_length=60, required=False)
    context = serializers.DictField(required=False, help_text="Para responder a uma mensagem específica")

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Validar total de rows <= 10
        total_rows = sum(len(section["rows"]) for section in attrs.get("sections", []))
        if total_rows > 10:
            raise serializers.ValidationError({"sections": "Total de itens não pode exceder 10"})
        return attrs
