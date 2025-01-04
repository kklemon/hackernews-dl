hackernews-dl
=============

Simple Python script to download Hackernews items into an SQL database using the [official API](https://github.com/HackerNews/API)

Usage
-----

Clone repository:

```bash
git clone git@github.com:kklemon/hackernews-dl.git
```

Install package and dependencies:

```bash
pip install .
```

Run download script:

```bash
hackernews-dl \
    --db=sqlite:///hackernews.db \  # SQL database URL
    --parallel-downloads=128 \  # Number of parallel downloads
    --max-items=None \  # Max items to download including existing ones if ignore_existing=True
    --min-item-id=None \  # Minimum item ID to start from
    --descending=True \  # Whether to download in descending order, i.e. newest first
    --ignore-existing=True \  # Ignore item IDs which are already present in the database
    --commit-every=1024 \  # Database commit frequency
```


The items will be followed in a table with the following schema:

| Field       | Type            | Description                                                          |
|-------------|-----------------|----------------------------------------------------------------------|
| **id**      | `int`           | Primary key of the item.                                             |
| deleted     | `bool`          | Indicates if the item was deleted.                                   |
| type        | `str`           | The type of the item (e.g., "story", "comment").                     |
| time        | `int`           | Unix time at which the item was created.                             |
| by          | `str`           | Username of the item's author.                                       |
| text        | `str`           | Content of the item (for comments, the comment text).                |
| dead        | `bool`          | Indicates if the item is dead.                                       |
| parent      | `int`           | ID of the parent item (e.g., the story that a comment belongs to).   |
| poll        | `int`           | If the item is a poll, this is its parent poll's ID.                 |
| kids        | `list[Self]     | The item's comments, in ranked display order.                        |
| url         | `str`           | URL associated with the item (typically for stories).                |
| score       | `int`           | Score of the item.                                                   |
| title       | `str`           | Title of the item (for stories or polls).                            |
| descendants | `int`           | Number of descendants of the item (comments).                        |

All fields except **id** are optional.

Ideas for improvement
---------------------

- [ ] All IDs to download are submitted at once to the executor which may result in unncessary high memory usage. We should instead start n download workers which pop IDs from a shared queue.
* [ ] Move writing and committing to the workers to aleviate the bottleneck in the main thread.
* [x] Model the item-kids relation in the schema