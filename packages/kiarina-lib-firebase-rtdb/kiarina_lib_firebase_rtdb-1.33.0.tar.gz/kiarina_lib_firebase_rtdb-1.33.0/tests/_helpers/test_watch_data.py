import asyncio


from kiarina.lib.firebase.rtdb import DataChangeEvent, watch_data


async def test_unauthorized(database_url, token_manager) -> None:
    # In unauthorized case, the stream does not end
    async def _task():
        async for _ in watch_data(database_url, "/posts/other_user", token_manager):
            pass

    watch_task = asyncio.create_task(_task())

    try:
        await asyncio.wait_for(watch_task, timeout=1.0)
    except asyncio.TimeoutError:
        watch_task.cancel()

        try:
            await watch_task
        except asyncio.CancelledError:
            pass


async def test_happy_path(database_url, user_id, token_manager) -> None:
    events: list[DataChangeEvent] = []
    stop_event = asyncio.Event()

    async def _task():
        nonlocal events

        async for event in watch_data(
            database_url,
            f"/posts/{user_id}",
            token_manager,
            stop_event=stop_event,
        ):
            assert event.event_type == "put"
            assert isinstance(event.data, dict)
            assert event.data.get("content") == "hello"

            events.append(event)

    watch_task = asyncio.create_task(_task())

    await asyncio.sleep(1)

    stop_event.set()

    try:
        # Normally stops on keep-alive event,
        # but it takes time, so stop with timeout
        await asyncio.wait_for(watch_task, timeout=2.0)

    except asyncio.TimeoutError:
        watch_task.cancel()

        try:
            await watch_task
        except asyncio.CancelledError:
            pass

    assert len(events) > 0
