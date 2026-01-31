from django.db import models

from .core import WebhookEvent


class MessageText(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_text")
    body = models.TextField()

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Text"
        verbose_name_plural = "Message Texts"


class MessageReaction(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_reaction")
    reacted_message_id = models.CharField(max_length=128)
    emoji = models.CharField(max_length=32)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Reaction"
        verbose_name_plural = "Message Reactions"


class MessageMedia(models.Model):
    TYPE_IMAGE = "image"
    TYPE_AUDIO = "audio"
    TYPE_VIDEO = "video"
    TYPE_DOCUMENT = "document"
    TYPE_STICKER = "sticker"
    TYPE_CHOICES = [
        (TYPE_IMAGE, "Image"),
        (TYPE_AUDIO, "Audio"),
        (TYPE_VIDEO, "Video"),
        (TYPE_DOCUMENT, "Document"),
        (TYPE_STICKER, "Sticker"),
    ]

    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_media")
    media_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    media_id = models.CharField(max_length=128)
    mime_type = models.CharField(max_length=128, null=True, blank=True)
    sha256 = models.CharField(max_length=128, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Media"
        verbose_name_plural = "Message Media"


class MessageLocation(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_location")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=512, null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Location"
        verbose_name_plural = "Message Locations"


class MessageContacts(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_contacts")
    contacts = models.JSONField()

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Contacts"
        verbose_name_plural = "Message Contacts"


class MessageSystem(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_system")
    system_type = models.CharField(max_length=64)
    body = models.TextField(null=True, blank=True)
    new_wa_id = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message System"
        verbose_name_plural = "Message Systems"


class MessageOrder(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_order")
    order = models.JSONField()

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Order"
        verbose_name_plural = "Message Orders"


class MessageInteractive(models.Model):
    """
    Stores interactive message responses (button clicks and list selections).

    interactive_type can be:
    - 'button_reply': User clicked a quick reply button
    - 'list_reply': User selected an item from a list menu
    """
    TYPE_BUTTON_REPLY = "button_reply"
    TYPE_LIST_REPLY = "list_reply"
    TYPE_CHOICES = [
        (TYPE_BUTTON_REPLY, "Button Reply"),
        (TYPE_LIST_REPLY, "List Reply"),
    ]

    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_interactive")
    interactive_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    reply_id = models.CharField(max_length=256, help_text="The ID of the button or list item selected")
    reply_title = models.CharField(max_length=256, help_text="The title/text of the selected option")
    reply_description = models.TextField(null=True, blank=True, help_text="Description (for list items only)")

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Interactive"
        verbose_name_plural = "Message Interactive"


class MessageUnknown(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_unknown")
    errors = models.JSONField(null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Unknown"
        verbose_name_plural = "Message Unknown"


