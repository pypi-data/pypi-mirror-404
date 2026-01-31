from typing import Dict

import requests
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.http import HttpResponse
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

from ....authentication.base import BaseAuthenticatedAPIView
from ....mixins import TenantMixin
from ....utils import get_business_by_tenant
from .serializers import MediaUploadSerializer, MediaIdSerializer, MediaUrlDownloadSerializer
from ....models import WhatsAppCloudApiBusiness, MetaApp


def _build_media_upload_url(api_version: str, phone_number_id: str) -> str:
    return f"https://graph.facebook.com/{api_version}/{phone_number_id}/media"


def _build_media_id_url(api_version: str, media_id: str, phone_number_id: str | None = None) -> str:
    base = f"https://graph.facebook.com/{api_version}/{media_id}"
    if phone_number_id:
        return f"{base}?phone_number_id={phone_number_id}"
    return base


def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class MediaUploadView(TenantMixin, BaseAuthenticatedAPIView):
    def post(self, request):
        # Try to resolve business by tenant_id first (injected by TenantMiddleware)
        tenant_id = getattr(request, 'tenant_id', None)

        if tenant_id:
            # Resolve business by tenant - no sender_phone_number needed
            business = get_business_by_tenant(tenant_id)
            uploaded = request.FILES.get('file')
            if not uploaded:
                return Response(
                    {"error": "No file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Fallback: use sender_phone_number (legacy behavior)
            serializer = MediaUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            v = serializer.validated_data
            business = WhatsAppCloudApiBusiness.objects.get(phone_number=v["sender_phone_number"])
            uploaded = v["file"]

        url = _build_media_upload_url(business.api_version, business.phone_number_id)

        files = {
            # 'file' must include the filename and content-type for correct MIME handling
            "file": (uploaded.name, uploaded.file, uploaded.content_type or "application/octet-stream"),
        }
        data = {"messaging_product": "whatsapp"}

        resp = requests.post(url, headers=_auth_headers(business.token), files=files, data=data)
        body = resp.json() if resp.content else None
        return Response(body, status=resp.status_code)


class MediaGetUrlView(BaseAuthenticatedAPIView):
    def get(self, request, media_id: str):
        serializer = MediaIdSerializer(data={
            "sender_phone_number": request.query_params.get("sender_phone_number"),
            "media_id": media_id,
        })
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        business = WhatsAppCloudApiBusiness.objects.get(phone_number=v["sender_phone_number"])
        url = _build_media_id_url(business.api_version, v["media_id"], business.phone_number_id)
        resp = requests.get(url, headers=_auth_headers(business.token))
        body = resp.json() if resp.content else None
        return Response(body, status=resp.status_code)


class MediaDeleteView(BaseAuthenticatedAPIView):
    def delete(self, request, media_id: str):
        serializer = MediaIdSerializer(data={
            "sender_phone_number": request.query_params.get("sender_phone_number"),
            "media_id": media_id,
        })
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        business = WhatsAppCloudApiBusiness.objects.get(phone_number=v["sender_phone_number"])
        url = _build_media_id_url(business.api_version, v["media_id"], business.phone_number_id)
        resp = requests.delete(url, headers=_auth_headers(business.token))
        body = resp.json() if resp.content else None
        return Response(body, status=resp.status_code)


class MediaDownloadView(BaseAuthenticatedAPIView):
    def get(self, request):
        serializer = MediaUrlDownloadSerializer(data={
            "sender_phone_number": request.query_params.get("sender_phone_number"),
            "url": request.query_params.get("url"),
        })
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data

        business = WhatsAppCloudApiBusiness.objects.get(phone_number=v["sender_phone_number"])

        # media URLs expire after 5 minutes; simply forward the GET with auth header
        resp = requests.get(v["url"], headers=_auth_headers(business.token), stream=True)

        # On success, proxy back binary with content-type
        content = resp.content
        status_code = resp.status_code
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        disposition = resp.headers.get("Content-Disposition")

        django_resp = HttpResponse(content=content, status=status_code, content_type=content_type)
        if disposition:
            django_resp["Content-Disposition"] = disposition
        return django_resp


class ResumableUploadView(TenantMixin, BaseAuthenticatedAPIView):
    """
    Upload media using Meta's Resumable Upload API.

    This is required for template creation with IMAGE/DOCUMENT headers.
    Returns a 'handle' (h field) that can be used as header_handle in template creation.

    The process:
    1. Create upload session: POST /{app_id}/uploads
    2. Upload file data: POST /{upload_session_id}
    3. Return the handle from step 2
    """

    def post(self, request):
        tenant_id = getattr(request, 'tenant_id', None)

        if not tenant_id:
            return Response(
                {"error": "Tenant ID is required for resumable upload"},
                status=status.HTTP_400_BAD_REQUEST
            )

        business = get_business_by_tenant(tenant_id)
        uploaded = request.FILES.get('file')

        if not uploaded:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Read file content
        file_content = uploaded.read()
        file_length = len(file_content)
        file_name = uploaded.name
        file_type = uploaded.content_type or "application/octet-stream"

        # Get MetaApp for app_id (required for Resumable Upload API)
        meta_app = MetaApp.objects.first()
        if not meta_app:
            return Response(
                {"error": "MetaApp not configured. Please configure app_id in admin."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 1: Create upload session
        # POST https://graph.facebook.com/{api_version}/{app_id}/uploads
        app_id = meta_app.app_id
        api_version = business.api_version

        session_url = f"https://graph.facebook.com/{api_version}/{app_id}/uploads"
        session_params = {
            "file_length": file_length,
            "file_name": file_name,
            "file_type": file_type,
        }

        session_resp = requests.post(
            session_url,
            params=session_params,
            headers=_auth_headers(business.token)
        )

        if not session_resp.ok:
            return Response(
                session_resp.json() if session_resp.content else {"error": "Failed to create upload session"},
                status=session_resp.status_code
            )

        session_data = session_resp.json()
        upload_session_id = session_data.get("id")

        if not upload_session_id:
            return Response(
                {"error": "No upload session ID returned"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 2: Upload file data
        # POST https://graph.facebook.com/{api_version}/{upload_session_id}
        upload_url = f"https://graph.facebook.com/{api_version}/{upload_session_id}"

        upload_headers = {
            "Authorization": f"OAuth {business.token}",
            "file_offset": "0",
            "Content-Type": file_type,
        }

        upload_resp = requests.post(
            upload_url,
            headers=upload_headers,
            data=file_content
        )

        if not upload_resp.ok:
            return Response(
                upload_resp.json() if upload_resp.content else {"error": "Failed to upload file"},
                status=upload_resp.status_code
            )

        upload_data = upload_resp.json()
        handle = upload_data.get("h")

        if not handle:
            return Response(
                {"error": "No handle returned from upload", "response": upload_data},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Return the handle in a format consistent with other upload endpoints
        return Response({"id": handle}, status=status.HTTP_200_OK)


