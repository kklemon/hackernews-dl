from sqlalchemy import Engine
import typer
import json
import numpy as np
from tqdm import tqdm
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlmodel import SQLModel, Session, create_engine, select
from hn_sdk.client.v0.client import get_item_by_id, get_max_item_id
from hackernews_dl import utils
from hackernews_dl.models import HackerNewsItem


def download_and_save_item(item_id, item_folder):
    item = get_item_by_id(item_id)
    item_path = item_folder / f"{item_id}.json"
    item_path.write_text(json.dumps(item))


def get_existing_ids(engine):
    with Session(engine) as session:
        return session.exec(select(HackerNewsItem.id)).all()


def download(
    db: Engine,
    parallel_downloads: int = 16,
    max_items: int | None = None,
    min_item_id: int | None = None,
    descending: bool = True,
    ignore_existing: bool = True,
    commit_every: int = 1024,
    log_errors: bool = False,
):
    max_item_id = get_max_item_id()

    item_ids = np.arange(min_item_id or 1, max_item_id)

    if descending:
        item_ids = np.flip(item_ids)

    if max_items:
        item_ids = item_ids[:max_items]

    if ignore_existing:
        existing_ids = np.array(get_existing_ids(db))
        indices_to_delete = np.where(np.isin(item_ids, existing_ids))[0]
        item_ids = np.delete(item_ids, indices_to_delete)

        print(f"Skipping {len(existing_ids):,} items as they already exist in the database")

    with (
        ThreadPoolExecutor(max_workers=parallel_downloads) as executor,
        tqdm(total=len(item_ids)) as pbar,
        Session(db) as session,
    ):
        futures = []

        try:
            for item_id in item_ids:
                futures.append(executor.submit(get_item_by_id, item_id))

            success = failure = 0
            num_uncommitted = 0

            for future in as_completed(futures):
                try:
                    item_dict = future.result()
                    item = HackerNewsItem(
                        parent_id=item_dict.pop("parent", None),
                        **utils.remove_keys(item_dict, ["kids", "parts", "parent"]),
                    )
                    session.add(item)
                    
                    success += 1
                    num_uncommitted += 1
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    failure += 1

                    if log_errors:
                        print(f"Error: {e}")

                if num_uncommitted % commit_every == 0:
                    num_uncommitted = 0
                    session.commit()

                pbar.set_postfix(OrderedDict(ok=success, fail=failure))
                pbar.update(1)
        except KeyboardInterrupt:
            print("Cancelling all futures")

            for future in futures:
                future.cancel()
        finally:
            session.commit()


def main(
    db: str = "sqlite:///hackernews.db",
    parallel_downloads: int = 16,
    max_items: int | None = None,
    min_item_id: int | None = None,
    descending: bool = True,
    ignore_existing: bool = True,
    commit_every: int = 1024,
):
    engine = create_engine(db)
    SQLModel.metadata.create_all(engine)

    try:
        download(
            db=engine,
            parallel_downloads=parallel_downloads,
            max_items=max_items,
            min_item_id=min_item_id,
            descending=descending,
            ignore_existing=ignore_existing,
            commit_every=commit_every,
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    typer.run(main)
