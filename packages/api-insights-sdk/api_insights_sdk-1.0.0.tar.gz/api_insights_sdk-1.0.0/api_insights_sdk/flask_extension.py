"""
Flask Extension for automatic API tracking.

Automatically captures raw HTTP request/response metadata and sends it
to the API Insights server. The server derives all analytics.
"""

import logging
from datetime import datetime, timezone as dt_timezone
from typing import Optional, List, Dict
from flask import Flask, request, g

from .tracker import APIInsightsTracker

logger = logging.getLogger(__name__)


class APIInsightsFlask:
    """
    Flask extension for automatic API request tracking.

    Captures raw HTTP request/response metadata and sends it to
    API Insights. The server extracts and computes all analytics.

    Usage:
        from flask import Flask
        from api_insights_sdk.flask_extension import APIInsightsFlask

        app = Flask(__name__)
        app.config['API_INSIGHTS_API_KEY'] = 'your_api_key'

        insights = APIInsightsFlask(app)
        # or
        insights = APIInsightsFlask()
        insights.init_app(app)
    """

    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.tracker: Optional[APIInsightsTracker] = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize the extension with a Flask application."""
        self.app = app

        # Get configuration
        api_key = app.config.get('API_INSIGHTS_API_KEY')
        if not api_key:
            logger.warning("API_INSIGHTS_API_KEY not configured. Tracking disabled.")
            return

        endpoint = app.config.get(
            'API_INSIGHTS_ENDPOINT',
            'https://api.yourservice.com/api/v1/track/'
        )

        self.tracker = APIInsightsTracker(api_key=api_key, endpoint=endpoint)

        # Get exclusion settings
        self.exclude_paths: List[str] = app.config.get('API_INSIGHTS_EXCLUDE_PATHS', [])
        self.track_only_api: bool = app.config.get('API_INSIGHTS_TRACK_ONLY_API', False)

        # Register hooks
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)

        # Store reference in app extensions
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['api_insights'] = self

    def _should_track(self) -> bool:
        """Check if current request should be tracked."""
        if not self.tracker:
            return False

        path = request.path

        # Check excluded paths
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False

        # Check if we only track API paths
        if self.track_only_api and not path.startswith('/api/'):
            return False

        return True

    def _before_request(self):
        """Store request start time and tracking flag."""
        g.api_insights_start_time = datetime.now(dt_timezone.utc)
        g.api_insights_should_track = self._should_track()

    def _after_request(self, response):
        """Track the request after response is ready."""
        if not getattr(g, 'api_insights_should_track', False):
            return response

        # Capture end time
        ended_at = datetime.now(dt_timezone.utc)
        started_at = getattr(g, 'api_insights_start_time', ended_at)

        # Extract raw HTTP metadata
        request_headers = self._extract_request_headers()
        response_headers = self._extract_response_headers(response)
        query_params = self._extract_query_params()

        # Calculate body sizes
        request_body_size = request.content_length or 0
        response_body_size = response.content_length or 0

        # Send raw HTTP metadata - server derives all analytics
        self.tracker.track(
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            started_at=started_at,
            ended_at=ended_at,
            request_headers=request_headers,
            response_headers=response_headers,
            query_params=query_params,
            request_body_size=request_body_size,
            response_body_size=response_body_size,
            ip_address=self._get_client_ip(),
            user_id=self._get_user_id(),
        )

        return response

    def _teardown_request(self, exception):
        """Handle exceptions and track failed requests."""
        if exception and getattr(g, 'api_insights_should_track', False):
            # Capture end time
            ended_at = datetime.now(dt_timezone.utc)
            started_at = getattr(g, 'api_insights_start_time', ended_at)

            # Extract raw HTTP metadata
            request_headers = self._extract_request_headers()
            query_params = self._extract_query_params()

            # Send raw HTTP metadata for error case
            self.tracker.track(
                method=request.method,
                path=request.path,
                status_code=500,
                started_at=started_at,
                ended_at=ended_at,
                request_headers=request_headers,
                response_headers={},
                query_params=query_params,
                request_body_size=request.content_length or 0,
                response_body_size=0,
                ip_address=self._get_client_ip(),
                user_id=self._get_user_id(),
                custom_data={'error_message': str(exception)},
            )

    def _extract_request_headers(self) -> Dict[str, str]:
        """Extract headers from Flask request."""
        headers = {}
        for key, value in request.headers:
            headers[key] = value
        return headers

    def _extract_response_headers(self, response) -> Dict[str, str]:
        """Extract headers from Flask response."""
        headers = {}
        for key, value in response.headers:
            headers[key] = value
        return headers

    def _extract_query_params(self) -> Dict[str, str]:
        """Extract query parameters from request."""
        params = dict(request.args)
        # Flatten single-value lists
        return {k: v[0] if isinstance(v, list) and len(v) == 1 else v
                for k, v in params.items()}

    def _get_client_ip(self) -> Optional[str]:
        """Extract client IP from request."""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return request.remote_addr

    def _get_user_id(self) -> Optional[str]:
        """Extract user ID from Flask-Login if available."""
        try:
            from flask_login import current_user
            if current_user.is_authenticated:
                return str(current_user.id)
        except ImportError:
            pass
        return None
