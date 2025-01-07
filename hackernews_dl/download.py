import asyncio
from sqlalchemy import Engine
import typer
from aiohttp import ClientSession
from tqdm import tqdm
from collections import OrderedDict
from sqlmodel import SQLModel, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine
from hackernews_dl import utils
from hackernews_dl.hn import HackerNewsClient
from hackernews_dl.models import HackerNewsItem


async def get_existing_ids(session):
    result = await session.exec(select(HackerNewsItem.id))
    return result.all()


async def download(
    db: Engine,
    concurrent_workers: int | None = 64,
    max_items: int | None = None,
    min_item_id: int | None = None,
    descending: bool = True,
    update_existing: bool = False,
    commit_every: int = 10_000,
    log_errors: bool = False,
):
    make_session = sessionmaker(db, class_=AsyncSession, expire_on_commit=False, autoflush=False)

    async with ClientSession() as http_session:
        hn = HackerNewsClient(session=http_session)

        max_item_id = await hn.get_max_item_id()

        item_ids = list(range(min_item_id or 1, max_item_id))

        if descending:
            item_ids = item_ids[::-1]

        if max_items:
            item_ids = item_ids[:max_items]

        async with make_session() as session:
            existing_ids = set(await get_existing_ids(session))

        if not update_existing:
            num_original = len(item_ids)

            item_ids = [item_id for item_id in item_ids if item_id not in existing_ids]

            print(
                f"Skipping {num_original - len(item_ids):,} items as they already exist in the database"
            )

        with tqdm(total=len(item_ids)) as pbar:
            success = failure = 0
            num_uncommitted = 0
            merges = []

            async with make_session() as session:
                try:
                    async for item_dict in utils.fetch_items(
                        hn, item_ids, concurrent_tasks=concurrent_workers
                    ):
                        try:
                            item = HackerNewsItem(
                                parent_id=item_dict.pop("parent", None),
                                **utils.remove_keys(item_dict, ["kids", "parts", "parent"]),
                            )

                            if item.id in existing_ids:
                                merges.append(session.merge(item))
                            else:
                                session.add(item)

                            success += 1
                        except KeyboardInterrupt:
                            raise
                        except Exception as e:
                            if log_errors:
                                print(f"Error with item {item.id}: {e}")
                            failure += 1

                        num_uncommitted += 1

                        if commit_every and num_uncommitted % commit_every == 0:
                            if merges:
                                await asyncio.gather(*merges)
                                merges.clear()
                            await session.commit()
                            num_uncommitted = 0

                        pbar.set_postfix(OrderedDict(ok=success, fail=failure))
                        pbar.update(1)
                except KeyboardInterrupt:
                    pass
                finally:
                    if merges:
                        await asyncio.gather(*merges)

                    await session.commit()


def main(
    db: str = "sqlite:///hackernews.db",
    concurrent_workers: int | None = 64,
    max_items: int | None = None,
    min_item_id: int | None = None,
    descending: bool = True,
    update_existing: bool = False,
    commit_every: int = 10_000,
    log_errors: bool = False,
):
    async def _main():
        engine = AsyncEngine(create_engine(db))

        async with engine.begin() as conn:
            # init db
            await conn.run_sync(SQLModel.metadata.create_all)

        try:
            await download(
                db=engine,
                concurrent_workers=concurrent_workers,
                max_items=max_items,
                min_item_id=min_item_id,
                descending=descending,
                update_existing=update_existing,
                commit_every=commit_every,
                log_errors=log_errors,
            )
        finally:
            await engine.dispose()

    asyncio.run(_main())


def run():
    typer.run(main)


if __name__ == "__main__":
    run()
