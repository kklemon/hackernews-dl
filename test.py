import asyncio
import aiohttp

from tqdm import tqdm
from aiostream import stream
from urllib.parse import urljoin
from hackernews_dl import utils
from hackernews_dl.hn import HackerNewsClient


async def main():
    num_fetch = 10_000

    async with aiohttp.ClientSession() as session:
        client = HackerNewsClient(session)
        # fetcher = utils.RecursiveItemFetcher(client)

        max_item_id = await client.get_max_item_id()

        item_ids = list(range(max_item_id, max_item_id - num_fetch, -1))

        items = []

        with tqdm(total=num_fetch) as pbar:
            async for item in utils.fetch_items(client, item_ids):
                items.append(item)

                pbar.update(1)

        print(f"Downloaded {len(items)} items")


if __name__ == "__main__":
    asyncio.run(main())
