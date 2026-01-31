import logging

from django.contrib import admin
from .models import WhatsAppCloudApiBusiness, MetaApp, MigrationIntent


@admin.register(WhatsAppCloudApiBusiness)
class WhatsAppCloudApiBusinessAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'waba_id', 'type', 'tenant_id', 'debug_mode', 'updated_at']
    list_filter = ['type', 'debug_mode', 'tenant_id']
    list_editable = ['debug_mode']  # Allows editing debug_mode directly in the list view
    search_fields = ['phone_number', 'waba_id', 'business_id', 'phone_number_id']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Identification', {
            'fields': ('phone_number', 'phone_number_id', 'waba_id', 'business_id', 'type')
        }),
        ('Authentication', {
            'fields': ('token', 'api_version', 'verify_token', 'code', 'auth_desired_pin')
        }),
        ('Multi-tenancy', {
            'fields': ('tenant_id',),
        }),
        ('Debug', {
            'fields': ('debug_mode',),
            'description': 'Enable to see detailed logs of WhatsApp API requests'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


admin.site.register(MetaApp)


@admin.register(MigrationIntent)
class MigrationIntentAdmin(admin.ModelAdmin):
    list_display = [
        "migration_intent_id",
        "source_waba_id",
        "destination_waba_id",
        "status",
        "tenant_id",
        "created_at",
    ]
    list_filter = ["status", "tenant_id", "created_at"]
    search_fields = [
        "migration_intent_id",
        "source_waba_id",
        "destination_waba_id",
        "solution_id",
    ]
    readonly_fields = ["created_at", "updated_at", "completed_at"]
    ordering = ["-created_at"]

# Import webhooks admin registrations so they are discovered
try:
    from .whatsapp_cloud_api.webhooks import admin as webhooks_admin  # noqa: F401
except Exception:
    logging.getLogger(__name__).exception("Failed to import webhooks admin")


    

    
