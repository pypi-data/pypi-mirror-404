"""
Django Middleware for automatic API tracking.

Automatically captures raw HTTP request/response metadata and sends it
to the API Insights server. The server derives all analytics.
"""

import logging
from datetime import datetime, timezone as dt_timezone
from typing import Optional, Dict
from django.conf import settings
from django.http import HttpRequest, HttpResponse

from .tracker import APIInsightsTracker

logger = logging.getLogger(__name__)


class APIInsightsMiddleware:
    """
    Django middleware for automatic API request tracking.

    Captures raw HTTP request/response metadata and sends it to
    API Insights. The server extracts and computes all analytics.

    Configuration in settings.py:
        API_INSIGHTS_API_KEY = 'your_api_key'
        API_INSIGHTS_ENDPOINT = 'https://api.yourservice.com/api/v1/track/'
        API_INSIGHTS_EXCLUDE_PATHS = ['/health', '/static']
        API_INSIGHTS_TRACK_ONLY_API = True  # Only track paths starting with /api/
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Initialize tracker
        api_key = getattr(settings, 'API_INSIGHTS_API_KEY', None)
        if not api_key:
            logger.warning("API_INSIGHTS_API_KEY not configured. Tracking disabled.")
            self.tracker = None
        else:
            endpoint = getattr(
                settings,
                'API_INSIGHTS_ENDPOINT',
                'https://api.yourservice.com/api/v1/track/'
            )
            self.tracker = APIInsightsTracker(api_key=api_key, endpoint=endpoint)

        self.exclude_paths = getattr(settings, 'API_INSIGHTS_EXCLUDE_PATHS', [])
        self.track_only_api = getattr(settings, 'API_INSIGHTS_TRACK_ONLY_API', False)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip if tracker not configured
        if not self.tracker:
            return self.get_response(request)

        # Check if we should track this request
        if not self._should_track(request):
            return self.get_response(request)

        # Capture start time
        started_at = datetime.now(dt_timezone.utc)

        try:
            response = self.get_response(request)
            return response
        finally:
            # Capture end time
            ended_at = datetime.now(dt_timezone.utc)

            # Get status code
            status_code = getattr(response, 'status_code', 500) if 'response' in locals() else 500

            # Extract raw HTTP metadata
            request_headers = self._extract_request_headers(request)
            response_headers = self._extract_response_headers(response) if 'response' in locals() else {}
            query_params = self._extract_query_params(request)

            # Calculate body sizes
            request_body_size = len(request.body) if request.body else 0
            response_body_size = 0
            if 'response' in locals() and hasattr(response, 'content'):
                response_body_size = len(response.content)

            # Send raw HTTP metadata - server derives all analytics
            self.tracker.track(
                method=request.method,
                path=request.path,
                status_code=status_code,
                started_at=started_at,
                ended_at=ended_at,
                request_headers=request_headers,
                response_headers=response_headers,
                query_params=query_params,
                request_body_size=request_body_size,
                response_body_size=response_body_size,
                ip_address=self._get_client_ip(request),
                user_id=self._get_user_id(request),
            )

    def _should_track(self, request: HttpRequest) -> bool:
        """Check if this request should be tracked."""
        path = request.path

        # Check excluded paths
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False

        # Check if we only track API paths
        if self.track_only_api and not path.startswith('/api/'):
            return False

        return True

    def _extract_request_headers(self, request: HttpRequest) -> Dict[str, str]:
        """Extract headers from Django request."""
        headers = {}

        if hasattr(request, 'headers'):
            # Django 2.2+ has request.headers
            for key, value in request.headers.items():
                headers[key] = value
        else:
            # Fallback for older Django versions
            for key, value in request.META.items():
                if key.startswith('HTTP_'):
                    header_name = key[5:].replace('_', '-').title()
                    headers[header_name] = value
                elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                    header_name = key.replace('_', '-').title()
                    headers[header_name] = value

        return headers

    def _extract_response_headers(self, response: HttpResponse) -> Dict[str, str]:
        """Extract headers from Django response."""
        headers = {}
        for key, value in response.items():
            headers[key] = value
        return headers

    def _extract_query_params(self, request: HttpRequest) -> Dict[str, str]:
        """Extract query parameters from request."""
        if not request.GET:
            return {}

        params = dict(request.GET)
        # Flatten single-value lists
        return {k: v[0] if len(v) == 1 else v for k, v in params.items()}

    def _get_client_ip(self, request: HttpRequest) -> Optional[str]:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def _get_user_id(self, request: HttpRequest) -> Optional[str]:
        """Extract user ID from request if authenticated."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return str(request.user.id)
        return None
