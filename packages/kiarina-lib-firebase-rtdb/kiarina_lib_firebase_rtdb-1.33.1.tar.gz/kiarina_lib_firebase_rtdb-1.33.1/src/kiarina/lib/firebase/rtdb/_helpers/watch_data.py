import asyncio
import json
import logging
from typing import Any, AsyncIterator, Literal, cast

import httpx
from kiarina.lib.firebase.auth import TokenManager

from .._exceptions.rtdb_stream_cancelled_error import RTDBStreamCancelledError
from .._schemas.data_change_event import DataChangeEvent
from .._settings import settings_manager

logger = logging.getLogger(__name__)


async def watch_data(
    database_url: str,
    path: str,
    token_manager: TokenManager,
    *,
    stop_event: asyncio.Event | None = None,
) -> AsyncIterator[DataChangeEvent]:
    """
    Watch Firebase Realtime Database data changes using Server-Sent Events.

    This function automatically handles:
    - Token refresh when authentication is revoked
    - Network errors with exponential backoff retry
    - Graceful shutdown via stop_event

    Args:
        database_url: Firebase database URL (e.g., "https://my-project.firebaseio.com")
        path: Database path to watch (e.g., "/notifications/user123")
        token_manager: TokenManager instance for automatic token refresh
        stop_event: Optional asyncio.Event to stop watching (keyword-only)

    Yields:
        DataChangeEvent: Data change events (put/patch only)

    Raises:
        RTDBStreamCancelledError: When stream is cancelled by server

    Example:
        >>> from kiarina.lib.firebase.auth import TokenManager
        >>> from kiarina.lib.firebase.rtdb import watch_data
        >>> import asyncio
        >>>
        >>> manager = TokenManager(refresh_token="...", api_key="...")
        >>> stop_event = asyncio.Event()
        >>>
        >>> async for event in watch_data(
        ...     "https://my-project.firebaseio.com",
        ...     "/notifications/user123",
        ...     manager,
        ...     stop_event=stop_event,
        ... ):
        ...     print(f"Changed: {event.path} = {event.data}")
        ...     if event.data == "stop":
        ...         stop_event.set()  # Stop watching
    """
    logger.debug(f"Starting watch on {path} in {database_url}")
    settings = settings_manager.get_settings()
    retry_delay = settings.initial_retry_delay

    while True:
        # Check stop event
        if stop_event and stop_event.is_set():
            logger.debug("Stop event set, exiting watch loop")
            break

        try:
            async for event in _watch_stream(
                database_url, path, token_manager, stop_event
            ):
                yield event
                # Reset retry delay on successful event
                retry_delay = settings.initial_retry_delay

            # Stream ended normally (shouldn't happen with Firebase RTDB)
            logger.warning("Stream ended normally, exiting watch loop")
            break

        except _AuthRevokedError:
            # Token expired, refresh and reconnect immediately
            logger.info("Auth revoked, refreshing token and reconnecting")
            await token_manager.refresh()
            retry_delay = settings.initial_retry_delay
            continue

        except (httpx.HTTPError, httpx.StreamError) as e:
            # Network error, retry with exponential backoff
            logger.warning(
                f"Network error during watch: {e}, retrying in {retry_delay}s"
            )
            await asyncio.sleep(retry_delay)
            retry_delay = min(
                retry_delay * settings.retry_delay_multiplier, settings.max_retry_delay
            )
            continue

        except Exception as e:
            logger.error(f"Unexpected error during watch: {e}")
            raise


async def _watch_stream(
    database_url: str,
    path: str,
    token_manager: TokenManager,
    stop_event: asyncio.Event | None = None,
) -> AsyncIterator[DataChangeEvent]:
    # Get current ID token
    id_token = await token_manager.get_id_token()

    # Construct URL
    url = f"{database_url.rstrip('/')}{path}.json"
    params = {"auth": id_token}
    headers = {"Accept": "text/event-stream"}

    async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
        async with client.stream(
            "GET", url, params=params, headers=headers
        ) as response:
            response.raise_for_status()

            # Process SSE stream
            async for event in _parse_sse_stream(response, stop_event):
                yield event


async def _parse_sse_stream(
    response: httpx.Response,
    stop_event: asyncio.Event | None = None,
) -> AsyncIterator[DataChangeEvent]:
    """
    Parse Server-Sent Events stream.

    See: https://firebase.google.com/docs/reference/rest/database
    """
    buffer = ""

    async for chunk in response.aiter_text():
        # Check stop event
        if stop_event and stop_event.is_set():
            logger.debug("Stop event set during stream parsing")
            return

        buffer += chunk
        lines = buffer.split("\n")

        # Keep the last incomplete line in buffer
        buffer = lines[-1]
        lines = lines[:-1]

        # Process complete lines
        event_type: str | None = None
        event_data: str | None = None

        for line in lines:
            line = line.strip()

            if not line:
                # Empty line indicates end of event
                if event_type is not None:
                    event = _handle_sse_event(event_type, event_data)

                    if event is not None:
                        yield event

                    # Reset for next event
                    event_type = None
                    event_data = None

                continue

            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                event_data = line[5:].strip()


def _handle_sse_event(
    event_type: str,
    event_data: str | None,
) -> DataChangeEvent | None:
    if event_type == "keep-alive":
        return None

    elif event_type == "cancel":  # pragma: no cover
        raise RTDBStreamCancelledError(f"Stream cancelled: {event_data}")

    elif event_type == "auth_revoked":  # pragma: no cover
        raise _AuthRevokedError()

    elif event_type in ("put", "patch"):
        parsed_data = _parse_event_data(event_data)
        event_path = parsed_data.get("path", "")
        data = parsed_data.get("data")

        return DataChangeEvent(
            event_type=cast(Literal["put", "patch"], event_type),
            path=event_path,
            data=data,
        )

    else:  # pragma: no cover
        logger.warning(f"Unknown event type: {event_type}, data: {event_data}")
        return None


def _parse_event_data(event_data: str | None) -> dict[str, Any]:
    if not event_data:
        return {}

    try:
        parsed = json.loads(event_data)

        if not isinstance(parsed, dict):
            logger.warning(
                f"Event data is not a dict: {type(parsed)}, data: {event_data}"
            )
            return {}

        return parsed

    except json.JSONDecodeError as e:  # pragma: no cover
        logger.warning(f"Failed to parse event data: {e}, data: {event_data}")
        return {}


class _AuthRevokedError(Exception):
    pass
