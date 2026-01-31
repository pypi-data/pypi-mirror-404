"""
Requests hooks for WhatsApp Cloud API debugging.

This module provides automatic logging for all HTTP requests made to the WhatsApp API
when debug_mode is enabled on the WhatsAppCloudApiBusiness model.

Note: Logs include data directly in the message (not in extra dict) to ensure
compatibility with Sentry and other logging tools that don't capture extra fields.
"""
import json
import logging

logger = logging.getLogger(__name__)


def whatsapp_debug_hook(response, *args, **kwargs):
    """
    Hook that automatically logs request/response details.

    This hook is called after every request made through the WhatsApp client's session.
    It logs detailed information useful for debugging API issues.

    The hook checks the debug_mode flag passed via the request's context.
    """
    # Get debug_mode from the request context (set by the client)
    debug_mode = getattr(response, '_debug_mode', False)

    if not debug_mode:
        return response

    request = response.request

    # Prepare request data
    request_data = {
        'direction': 'request',
        'url': request.url,
        'method': request.method,
        'headers': dict(request.headers),
        'body': request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body,
    }

    # Log request with data in message (not in extra - Sentry doesn't capture extra)
    logger.info(f"WhatsApp API Request: {json.dumps(request_data, indent=2)}")

    # Prepare response data
    response_data = {
        'direction': 'response',
        'url': request.url,
        'status_code': response.status_code,
        'headers': dict(response.headers),
        'body': response.text,
    }

    # Log response with data in message
    logger.info(f"WhatsApp API Response: {json.dumps(response_data, indent=2)}")

    return response


class DebugSession:
    """
    A wrapper around requests that adds debug logging via hooks.

    Usage:
        session = DebugSession(debug_mode=True)
        response = session.post(url, json=payload, headers=headers)
    """

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode

    def request(self, method: str, url: str, **kwargs):
        """Make an HTTP request with optional debug logging."""
        import requests

        response = requests.request(method, url, **kwargs)

        # Attach debug_mode to response for the hook
        response._debug_mode = self.debug_mode

        # Call the hook manually (since we're not using a real Session with hooks)
        whatsapp_debug_hook(response)

        return response

    def get(self, url: str, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request('POST', url, **kwargs)

    def put(self, url: str, **kwargs):
        return self.request('PUT', url, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.request('DELETE', url, **kwargs)
