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


def main(
    db: str = "sqlite:///hackernews.db",
    parallel_downloads: int = 128,
    max_items: int | None = None,
    descending: bool = True,
    ignore_existing: bool = True,
):
    engine = create_engine(db)
    SQLModel.metadata.create_all(engine)

    max_item_id = get_max_item_id()

    item_ids = np.arange(1, max_item_id)

    if descending:
        item_ids = np.flip(item_ids)

    if max_items:
        item_ids = item_ids[:max_items]

    if ignore_existing:
        existing_ids = np.array(get_existing_ids(engine))
        indices_to_delete = np.where(np.isin(item_ids, existing_ids))[0]
        item_ids = np.delete(item_ids, indices_to_delete)

        print(f"Skipping {len(existing_ids)} items as they already exist in the database")

    with ThreadPoolExecutor(max_workers=parallel_downloads) as executor:
        futures = [executor.submit(get_item_by_id, item_id) for item_id in item_ids.tolist()]

        success = failure = 0

        with tqdm(total=len(item_ids)) as pbar, Session(engine) as session:
            try:
                for future in as_completed(futures):
                    try:
                        item_dict = future.result()
                        item = HackerNewsItem(**utils.remove_keys(item_dict, ["kids", "parts"]))
                        session.add(item)
                        success += 1
                    except:
                        failure += 1

                    pbar.set_postfix(OrderedDict(ok=success, fail=failure))
                    pbar.update(1)
            finally:
                session.commit()


if __name__ == "__main__":
    typer.run(main)
