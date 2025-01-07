from contextlib import nullcontext
from asyncio import Semaphore
from aiohttp import ClientSession
from urllib.parse import urljoin


class HackerNewsClient:
    def __init__(
        self,
        session: ClientSession,
        base_url: str = " https://hacker-news.firebaseio.com/v0/",
        concurrent_requests: int | None = None,
    ):
        self.session = session
        self.base_url = base_url

        if concurrent_requests:
            self.semaphore = Semaphore(concurrent_requests)
        else:
            self.semaphore = nullcontext()

    async def _get(self, endpoint: str):
        async with (
            self.semaphore,
            self.session.get(urljoin(self.base_url, endpoint), timeout=15) as response,
        ):
            return await response.json()

    async def get_max_item_id(self):
        return await self._get("maxitem.json")

    async def get_item_by_id(self, item_id: int):
        return await self._get(f"item/{item_id}.json")
