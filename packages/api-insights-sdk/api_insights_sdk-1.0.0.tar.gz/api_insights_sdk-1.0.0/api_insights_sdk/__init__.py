"""
API Insights SDK - Python decorator for tracking API requests.

Supports Django, Flask, FastAPI, and any Python HTTP framework.

Usage:
    from api_insights_sdk import APIInsightsTracker, track_api

    # Initialize the tracker with your API key
    tracker = APIInsightsTracker(api_key='your_api_key')

    # Use the decorator on your endpoints
    @app.route('/users')
    @track_api(tracker)
    def get_users():
        return {'users': []}

Django Middleware:
    MIDDLEWARE = [
        'sdk.django_middleware.APIInsightsMiddleware',
    ]
    API_INSIGHTS_API_KEY = 'your_api_key'

Flask Extension:
    from sdk.flask_extension import APIInsightsFlask
    insights = APIInsightsFlask(app)
"""

from .tracker import APIInsightsTracker, track_api

__all__ = [
    'APIInsightsTracker',
    'track_api',
]
__version__ = '1.0.0'
__author__ = 'API Insights'
__license__ = 'MIT'
