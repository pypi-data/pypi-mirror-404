"""
Example script to test watch_data functionality.

Usage:
    python examples/watch_example.py
"""

import asyncio
from typing import Any

from kiarina.lib.firebase.rtdb._utils.watch_data import watch_data


def on_event(event_type: str, path: str, data: Any) -> None:
    """Callback function for SSE events."""
    print(f"\n{'='*60}")
    print(f"Event Type: {event_type}")
    print(f"Path: {path}")
    print(f"Data: {data}")
    print(f"{'='*60}")


async def main():
    # TODO: Replace with your actual values
    database_url = "https://your-project.firebaseio.com"
    id_token = "your_id_token_here"
    watch_path = "/test"

    print(f"Starting to watch: {database_url}{watch_path}")
    print("Press Ctrl+C to stop\n")

    try:
        await watch_data(
            path=watch_path,
            id_token=id_token,
            database_url=database_url,
            callback=on_event,
        )
    except KeyboardInterrupt:
        print("\nStopped watching")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
