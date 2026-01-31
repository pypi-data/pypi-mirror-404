# kiarina-lib-firebase-rtdb

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](../../LICENSE)

> Firebase Realtime Database integration library with automatic token management and real-time data watching capabilities.

## Purpose

`kiarina-lib-firebase-rtdb` provides a simple and efficient way to interact with Firebase Realtime Database using REST APIs. This library focuses on real-time data watching with automatic token refresh and robust error handling.

Key features include:
- Real-time data watching with Server-Sent Events (SSE)
- Automatic ID token refresh via `TokenManager` integration
- Network error handling with exponential backoff retry
- Simple data retrieval operations
- Configuration management using pydantic-settings-manager
- Type-safe with full type hints
- Async-only API for modern Python applications

## Installation

```bash
pip install kiarina-lib-firebase-rtdb

# Or with uv
uv add kiarina-lib-firebase-rtdb
```

## Quick Start

### Basic Data Retrieval

```python
from kiarina.lib.firebase.auth import TokenManager
from kiarina.lib.firebase.rtdb import get_data

# Setup token manager
token_manager = TokenManager(
    refresh_token="your_refresh_token",
    api_key="your_firebase_api_key"
)

# Get data from database
data = await get_data(
    database_url="https://your-project.firebaseio.com",
    path="/users/user123",
    id_token=await token_manager.get_id_token()
)

print(data)  # {"name": "John", "age": 30}
```

### Real-time Data Watching

```python
import asyncio
from kiarina.lib.firebase.auth import TokenManager
from kiarina.lib.firebase.rtdb import watch_data

# Setup token manager
token_manager = TokenManager(
    refresh_token="your_refresh_token",
    api_key="your_firebase_api_key"
)

# Watch data changes
stop_event = asyncio.Event()

async for event in watch_data(
    database_url="https://your-project.firebaseio.com",
    path="/notifications/user123",
    token_manager=token_manager,
    stop_event=stop_event
):
    print(f"Event: {event.event_type}")
    print(f"Path: {event.path}")
    print(f"Data: {event.data}")
    
    # Stop watching when needed
    if event.data == "stop":
        stop_event.set()
```

## API Reference

### get_data()

Get data from Firebase Realtime Database.

```python
async def get_data(
    database_url: str,
    path: str,
    id_token: str,
) -> Any
```

**Parameters:**
- `database_url`: Firebase database URL (e.g., "https://my-project.firebaseio.com")
- `path`: Database path to get data from (e.g., "/users/user123")
- `id_token`: Firebase ID token for authentication

**Returns:**
- Data at the specified path (dict, list, str, int, float, bool, or None)

**Raises:**
- `httpx.HTTPError`: If request fails

### watch_data()

Watch Firebase Realtime Database data changes using Server-Sent Events.

```python
async def watch_data(
    database_url: str,
    path: str,
    token_manager: TokenManager,
    *,
    stop_event: asyncio.Event | None = None,
) -> AsyncIterator[DataChangeEvent]
```

**Parameters:**
- `database_url`: Firebase database URL (e.g., "https://my-project.firebaseio.com")
- `path`: Database path to watch (e.g., "/notifications/user123")
- `token_manager`: TokenManager instance for automatic token refresh
- `stop_event`: Optional asyncio.Event to stop watching (keyword-only)

**Yields:**
- `DataChangeEvent`: Data change events (put/patch only)

**Raises:**
- `RTDBStreamCancelledError`: When stream is cancelled by server

**Features:**
- Automatic token refresh when authentication is revoked
- Network error handling with exponential backoff retry
- Graceful shutdown via stop_event

### DataChangeEvent

Represents a data change event from Firebase RTDB.

```python
@dataclass
class DataChangeEvent:
    event_type: Literal["put", "patch"]
    path: str
    data: Any
```

**Fields:**
- `event_type`: Type of change ("put" for full update, "patch" for partial update)
- `path`: Path where the change occurred
- `data`: Changed data

### RTDBStreamCancelledError

Exception raised when RTDB stream is cancelled by server.

```python
class RTDBStreamCancelledError(Exception):
    pass
```

## Configuration

### Using pydantic-settings-manager

```python
from pydantic_settings_manager import load_user_configs

# Load from YAML configuration
config = {
    "kiarina.lib.firebase.rtdb": {
        "default": {
            "max_retry_delay": 60.0,
            "initial_retry_delay": 1.0,
            "retry_delay_multiplier": 2.0
        }
    }
}

load_user_configs(config)
```

### YAML Configuration Example

```yaml
kiarina.lib.firebase.rtdb:
  default:
    max_retry_delay: 60.0
    initial_retry_delay: 1.0
    retry_delay_multiplier: 2.0
```

### Environment Variables

```bash
# Retry configuration
KIARINA_LIB_FIREBASE_RTDB_MAX_RETRY_DELAY=60.0
KIARINA_LIB_FIREBASE_RTDB_INITIAL_RETRY_DELAY=1.0
KIARINA_LIB_FIREBASE_RTDB_RETRY_DELAY_MULTIPLIER=2.0
```

### RTDBSettings

Configuration model for Firebase Realtime Database operations.

```python
class RTDBSettings(BaseSettings):
    max_retry_delay: float = 60.0
    initial_retry_delay: float = 1.0
    retry_delay_multiplier: float = 2.0
```

**Fields:**
- `max_retry_delay`: Maximum delay between retries in seconds (default: 60.0)
- `initial_retry_delay`: Initial delay between retries in seconds (default: 1.0)
- `retry_delay_multiplier`: Exponential backoff multiplier for retry delays (default: 2.0)

## Advanced Usage

### Custom Stop Logic

```python
import asyncio
from kiarina.lib.firebase.rtdb import watch_data

stop_event = asyncio.Event()

async def watch_with_timeout():
    # Stop after 60 seconds
    await asyncio.sleep(60)
    stop_event.set()

# Start watching
watch_task = asyncio.create_task(watch_with_timeout())

async for event in watch_data(
    database_url="https://your-project.firebaseio.com",
    path="/data",
    token_manager=token_manager,
    stop_event=stop_event
):
    print(f"Event: {event.event_type}, Data: {event.data}")

await watch_task
```

### Error Handling

```python
from kiarina.lib.firebase.rtdb import watch_data, RTDBStreamCancelledError
import httpx

try:
    async for event in watch_data(
        database_url="https://your-project.firebaseio.com",
        path="/data",
        token_manager=token_manager
    ):
        print(f"Event: {event.event_type}")
        
except RTDBStreamCancelledError as e:
    print(f"Stream cancelled: {e}")
    
except httpx.HTTPError as e:
    print(f"HTTP error: {e}")
```

## Testing

### Setup Test Environment

1. Copy sample files:
```bash
cp .env.sample .env
cp test_settings.sample.yaml test_settings.yaml
```

2. Configure your Firebase project:
```bash
# .env
KIARINA_LIB_FIREBASE_RTDB_TEST_SETTINGS_FILE=/path/to/test_settings.yaml
KIARINA_LIB_FIREBASE_RTDB_TEST_DATABASE_URL=https://your-database.firebaseio.com/
```

3. Update test_settings.yaml with your credentials:
```yaml
kiarina.lib.google.auth:
  default:
    type: service_account
    project_id: your-project-id
    service_account_email: your-service-account@your-project.iam.gserviceaccount.com
    service_account_file: ~/.gcp/service-account/your-project/key.json

kiarina.lib.firebase.auth:
  default:
    project_id: your-project-id
    api_key: your-firebase-api-key

kiarina.lib.firebase.rtdb:
  default:
    database_url: https://your-project.firebaseio.com
    api_key: your-firebase-api-key
```

4. Configure Firebase Realtime Database security rules:
```json
{
  "rules": {
    ".read": false,
    ".write": false,
    "posts": {
      "$user_id": {
        ".read": "auth != null && auth.uid == $user_id",
        ".write": "auth != null && auth.uid == $user_id"
      }
    }
  }
}
```

5. Add test data to `/posts/test_user`:
```json
{"content": "hello"}
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kiarina.lib.firebase.rtdb --cov-report=html

# Run specific test
pytest tests/_helpers/test_watch_data.py -v
```

## Dependencies

- **httpx**: HTTP client for async requests
- **kiarina-lib-firebase-auth**: Firebase authentication with automatic token management
- **pydantic**: Data validation and settings management
- **pydantic-settings**: Settings management from environment variables
- **pydantic-settings-manager**: Multi-configuration settings management

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Related Projects

- [kiarina-lib-firebase-auth](../kiarina-lib-firebase-auth/) - Firebase authentication library
- [kiarina-lib-google-auth](../kiarina-lib-google-auth/) - Google Cloud authentication library
- [kiarina-python](https://github.com/kiarina/kiarina-python) - Parent monorepo

## Resources

- [Firebase Realtime Database REST API](https://firebase.google.com/docs/reference/rest/database)
- [Firebase Realtime Database Security Rules](https://firebase.google.com/docs/database/security)
- [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
