import asyncio
from typing import Any
from hackernews_dl.hn import HackerNewsClient


def remove_keys(d: dict, remove_keys: list[Any]):
    for key in remove_keys:
        d.pop(key, None)
    return d


async def fetch_items(client: HackerNewsClient, item_ids: list[int], concurrent_tasks: int = 100):
    inputs = asyncio.Queue()
    results = asyncio.Queue()

    signal = object()

    for item in item_ids:
        await inputs.put(item)

    async def worker():
        try:
            while True:
                try:
                    item_id = inputs.get_nowait()
                except asyncio.QueueEmpty:
                    break

                item = await client.get_item_by_id(item_id)

                await results.put(item)
        finally:
            await results.put(signal)

    tasks = [asyncio.create_task(worker()) for _ in range(concurrent_tasks)]

    n = len(tasks)

    try:
        while n:
            item = await results.get()

            if item is signal:
                n -= 1
            else:
                yield item
    except:
        for task in tasks:
            task.cancel()
        raise

    await asyncio.wait(tasks)
