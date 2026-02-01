# API Insights SDK

[![PyPI version](https://badge.fury.io/py/api-insights-sdk.svg)](https://badge.fury.io/py/api-insights-sdk)
[![Python versions](https://img.shields.io/pypi/pyversions/api-insights-sdk.svg)](https://pypi.org/project/api-insights-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight Python SDK for tracking and monitoring API requests across Django, Flask, FastAPI, and other Python HTTP frameworks. The SDK automatically collects HTTP request/response metadata and sends it to the API Insights server for comprehensive analytics and insights.

## Features

- **Multi-Framework Support**: Works seamlessly with Django, Flask, FastAPI, and any Python HTTP framework
- **Automatic Tracking**: Minimal code changes required - use decorators or middleware
- **Async Processing**: Background worker thread for non-blocking data transmission
- **Configurable Batching**: Efficient batch processing of request metadata
- **Low Overhead**: Minimal performance impact on your applications
- **Python 3.8+**: Compatible with modern Python versions

## Installation

Install the SDK using pip:

```bash
pip install api-insights-sdk
```

## Quick Start

### Basic Usage with Decorator

```python
from api_insights_sdk import APIInsightsTracker, track_api

# Initialize the tracker
tracker = APIInsightsTracker(api_key='your_api_key')

# Use the decorator on your endpoints
@app.route('/users')
@track_api(tracker)
def get_users():
    return {'users': []}
```

### Django Integration

Add the middleware to your `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware
    'sdk.django_middleware.APIInsightsMiddleware',
]

# Configure your API key
API_INSIGHTS_API_KEY = 'your_api_key'
```

### Flask Integration

```python
from flask import Flask
from sdk.flask_extension import APIInsightsFlask

app = Flask(__name__)
insights = APIInsightsFlask(app, api_key='your_api_key')

@app.route('/users')
def get_users():
    return {'users': []}
```

## Configuration

### APIInsightsTracker Parameters

```python
tracker = APIInsightsTracker(
    api_key='your_api_key',                    # Your API Insights project key
    endpoint='https://api.yourservice.com/api/v1/track/',  # Tracking endpoint
    batch_size=100,                             # Requests to batch before sending
    flush_interval=5.0,                         # Seconds between auto-flushes
    async_mode=True,                            # Enable async processing
    timeout=5.0,                                # Request timeout in seconds
)
```

## How It Works

1. **Request Capture**: The SDK intercepts HTTP requests and responses
2. **Metadata Collection**: Raw HTTP metadata is collected (headers, status codes, latency, etc.)
3. **Batching**: Requests are batched for efficient transmission
4. **Async Transmission**: Data is sent to the API Insights server in the background
5. **Server-Side Analytics**: The API Insights server processes the raw data to generate insights and analytics

## API Key

To use the API Insights SDK, you need an API key from your API Insights project. You can obtain this from your API Insights dashboard.

## Performance Considerations

- **Asynchronous Processing**: By default, the SDK uses a background worker thread to send data without blocking your application
- **Batch Processing**: Configure `batch_size` and `flush_interval` based on your traffic patterns
- **Minimal Overhead**: The SDK is designed to have minimal impact on your application's performance

## Error Handling

The SDK gracefully handles network errors and timeouts:

- Failed requests are logged but do not affect your application
- Errors are reported via Python's standard logging module

```python
import logging

# Enable debug logging to see SDK operations
logging.getLogger('api_insights_sdk').setLevel(logging.DEBUG)
```

## Supported Frameworks

- **Django**: Via middleware integration
- **Flask**: Via extension wrapper
- **FastAPI**: Via decorator support
- **Any WSGI/ASGI Application**: Via the decorator pattern

## Python Versions

The SDK requires Python 3.8 or higher.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, feature requests, or questions, please visit our [GitHub repository](https://github.com/yourusername/api-insights-sdk) or contact support at rahulrathod315@gmail.com.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### Version 1.0.0 (2026-01-31)

- Initial release
- Support for Django middleware
- Support for Flask extension
- Decorator-based tracking for any framework
- Async batch processing with configurable parameters
