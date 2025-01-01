from typing import Optional
from sqlmodel import Field, SQLModel


class HackerNewsItem(SQLModel, table=True):
    id: int = Field(primary_key=True)
    deleted: Optional[bool] = None
    type: Optional[str] = None
    time: Optional[int] = None
    by: Optional[str] = None
    text: Optional[str] = None
    dead: Optional[bool] = None
    parent: Optional[int] = None
    poll: Optional[int] = None
    url: Optional[str] = None
    score: Optional[int] = None
    title: Optional[str] = None
    descendants: Optional[int] = None
