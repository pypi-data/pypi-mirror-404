"""
API Insights Tracker - Core SDK implementation.

This module provides the tracker class that sends raw HTTP request/response
metadata to the API Insights server. The server derives all analytics.
"""

import time
import threading
import queue
import logging
import functools
from datetime import datetime, timezone as dt_timezone
from typing import Optional, Dict, Any, Callable
from urllib.request import Request, urlopen
from urllib.error import URLError
import json

logger = logging.getLogger(__name__)


class APIInsightsTracker:
    """
    Tracker class for sending HTTP request/response metadata to API Insights.

    This class handles batching and async sending of raw HTTP metadata.
    The server extracts and computes all analytics from the raw data.
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.yourservice.com/api/v1/track/",
        batch_size: int = 100,
        flush_interval: float = 5.0,
        async_mode: bool = True,
        timeout: float = 5.0,
    ):
        """
        Initialize the API Insights tracker.

        Args:
            api_key: Your API Insights project API key
            endpoint: The tracking endpoint URL
            batch_size: Number of requests to batch before sending
            flush_interval: Seconds between automatic flushes
            async_mode: Whether to send data asynchronously
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.endpoint = endpoint.rstrip('/')
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.async_mode = async_mode
        self.timeout = timeout

        self._queue: queue.Queue = queue.Queue()
        self._batch: list = []
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

        if async_mode:
            self._start_worker()

    def _start_worker(self):
        """Start the background worker thread."""
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def _worker(self):
        """Background worker that processes the queue."""
        last_flush = time.time()

        while self._running:
            try:
                # Try to get items from queue with timeout
                try:
                    item = self._queue.get(timeout=1.0)
                    with self._lock:
                        self._batch.append(item)
                    self._queue.task_done()
                except queue.Empty:
                    pass

                # Check if we should flush
                current_time = time.time()
                should_flush = (
                    len(self._batch) >= self.batch_size or
                    (len(self._batch) > 0 and current_time - last_flush >= self.flush_interval)
                )

                if should_flush:
                    self._flush_batch()
                    last_flush = current_time

            except Exception as e:
                logger.error(f"Worker error: {e}")

    def _flush_batch(self):
        """Send the current batch to the server."""
        with self._lock:
            if not self._batch:
                return
            batch_to_send = self._batch.copy()
            self._batch.clear()

        try:
            self._send_batch(batch_to_send)
        except Exception as e:
            logger.error(f"Failed to send batch: {e}")
            # Optionally re-queue failed items
            with self._lock:
                self._batch.extend(batch_to_send)

    def _send_batch(self, batch: list):
        """Send a batch of tracking data to the server."""
        if not batch:
            return

        url = f"{self.endpoint}/batch/"
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
        }
        data = json.dumps({'requests': batch}).encode('utf-8')

        request = Request(url, data=data, headers=headers, method='POST')

        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 201:
                    logger.warning(f"Unexpected status: {response.status}")
        except URLError as e:
            logger.error(f"Failed to send batch: {e}")
            raise

    def _send_single(self, data: dict):
        """Send a single tracking request to the server."""
        url = self.endpoint
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
        }
        payload = json.dumps(data).encode('utf-8')

        request = Request(url, data=payload, headers=headers, method='POST')

        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 201:
                    logger.warning(f"Unexpected status: {response.status}")
        except URLError as e:
            logger.error(f"Failed to send request: {e}")
            raise

    def track(
        self,
        method: str,
        path: str,
        status_code: int,
        started_at: datetime,
        ended_at: datetime,
        request_headers: Optional[Dict[str, str]] = None,
        response_headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        request_body_size: int = 0,
        response_body_size: int = 0,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        custom_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Track an HTTP request/response event.

        Sends raw HTTP metadata to the server, which extracts and computes
        all analytics (response_time_ms, user_agent, content_type, categories, etc.).

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., '/api/users/123')
            status_code: HTTP response status code
            started_at: Datetime when request processing started
            ended_at: Datetime when response was sent
            request_headers: HTTP request headers
            response_headers: HTTP response headers
            query_params: URL query parameters
            request_body_size: Size of request body in bytes
            response_body_size: Size of response body in bytes
            ip_address: Client IP address
            user_id: User identifier from client system
            custom_data: Additional custom metadata
        """
        # Build the HTTP metadata payload
        payload = {
            'request': {
                'method': method.upper(),
                'path': path,
                'query_params': query_params or {},
                'headers': request_headers or {},
                'body_size': request_body_size,
            },
            'response': {
                'status_code': status_code,
                'headers': response_headers or {},
                'body_size': response_body_size,
            },
            'client': {
                'ip_address': ip_address,
            },
            'timing': {
                'started_at': self._format_datetime(started_at),
                'ended_at': self._format_datetime(ended_at),
            },
            'context': {
                'user_id': user_id or '',
                'custom_data': custom_data or {},
            },
        }

        if self.async_mode:
            self._queue.put(payload)
        else:
            self._send_single(payload)

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime to ISO 8601 string with timezone."""
        if dt.tzinfo is None:
            # Assume UTC for naive datetimes
            dt = dt.replace(tzinfo=dt_timezone.utc)
        return dt.isoformat()

    def flush(self):
        """Force flush any pending tracking data."""
        if self.async_mode:
            # Wait for queue to empty
            self._queue.join()
            # Then flush the batch
            self._flush_batch()
        else:
            self._flush_batch()

    def shutdown(self):
        """Shutdown the tracker gracefully."""
        self._running = False
        self.flush()
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)


def track_api(
    tracker: APIInsightsTracker,
    get_user_id: Optional[Callable] = None,
):
    """
    Decorator to automatically track API requests.

    Wraps your API endpoint functions and automatically sends HTTP metadata
    to API Insights. The server extracts all analytics from the raw data.

    Args:
        tracker: An APIInsightsTracker instance
        get_user_id: Optional function to extract user ID from request

    Usage with Flask:
        @app.route('/api/users', methods=['GET'])
        @track_api(tracker)
        def get_users():
            return jsonify({'users': []})

    Usage with Django:
        @track_api(tracker)
        def my_view(request):
            return JsonResponse({'data': []})
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            started_at = datetime.now(dt_timezone.utc)
            status_code = 500
            response = None

            try:
                response = func(*args, **kwargs)

                # Try to extract status code from response
                if hasattr(response, 'status_code'):
                    status_code = response.status_code
                elif isinstance(response, tuple) and len(response) >= 2:
                    status_code = response[1]
                else:
                    status_code = 200

                return response

            except Exception:
                raise

            finally:
                ended_at = datetime.now(dt_timezone.utc)

                # Extract request info
                request_obj = None
                if args:
                    first_arg = args[0]
                    if hasattr(first_arg, 'path') and hasattr(first_arg, 'method'):
                        request_obj = first_arg

                if request_obj:
                    # Extract headers
                    request_headers = _extract_headers(request_obj)

                    # Extract response headers if available
                    response_headers = {}
                    if response and hasattr(response, 'headers'):
                        response_headers = dict(response.headers) if hasattr(response.headers, 'items') else {}

                    # Get user ID
                    user_id = None
                    if get_user_id:
                        user_id = get_user_id(request_obj)

                    # Track using raw HTTP metadata
                    tracker.track(
                        method=request_obj.method,
                        path=request_obj.path,
                        status_code=status_code,
                        started_at=started_at,
                        ended_at=ended_at,
                        request_headers=request_headers,
                        response_headers=response_headers,
                        query_params=_extract_query_params(request_obj),
                        request_body_size=_get_body_size(request_obj),
                        response_body_size=_get_response_size(response),
                        ip_address=_extract_ip(request_obj),
                        user_id=user_id,
                    )

        return wrapper
    return decorator


def _extract_headers(request) -> Dict[str, str]:
    """Extract headers from request object."""
    headers = {}

    if hasattr(request, 'headers'):
        # Flask/Django 2.2+ style
        if hasattr(request.headers, 'items'):
            for key, value in request.headers.items():
                headers[key] = value
        elif hasattr(request.headers, '__iter__'):
            for key, value in request.headers:
                headers[key] = value

    elif hasattr(request, 'META'):
        # Django style
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').title()
                headers[header_name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                header_name = key.replace('_', '-').title()
                headers[header_name] = value

    return headers


def _extract_query_params(request) -> Dict[str, Any]:
    """Extract query parameters from request object."""
    if hasattr(request, 'args'):
        # Flask style
        return dict(request.args)
    elif hasattr(request, 'GET'):
        # Django style
        params = dict(request.GET)
        # Flatten single-value lists
        return {k: v[0] if len(v) == 1 else v for k, v in params.items()}
    return {}


def _extract_ip(request) -> Optional[str]:
    """Extract client IP from request object."""
    # Try X-Forwarded-For header first
    if hasattr(request, 'headers'):
        xff = None
        if hasattr(request.headers, 'get'):
            xff = request.headers.get('X-Forwarded-For')
        if xff:
            return xff.split(',')[0].strip()

    if hasattr(request, 'META'):
        # Django request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    if hasattr(request, 'remote_addr'):
        # Flask style
        return request.remote_addr

    return None


def _get_body_size(request) -> int:
    """Get request body size."""
    if hasattr(request, 'content_length') and request.content_length:
        return request.content_length
    if hasattr(request, 'body'):
        return len(request.body) if request.body else 0
    return 0


def _get_response_size(response) -> int:
    """Get response body size."""
    if response is None:
        return 0
    if hasattr(response, 'content_length') and response.content_length:
        return response.content_length
    if hasattr(response, 'content'):
        return len(response.content) if response.content else 0
    return 0
