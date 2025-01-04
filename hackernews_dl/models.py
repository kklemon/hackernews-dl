from typing import Optional
from sqlalchemy.orm import backref
from sqlmodel import Field, Relationship, SQLModel


class HackerNewsItem(SQLModel, table=True):
    __tablename__ = "hackernewsitem"

    id: int = Field(primary_key=True)
    deleted: Optional[bool] = None
    type: Optional[str] = None
    time: Optional[int] = None
    by: Optional[str] = None
    text: Optional[str] = None
    dead: Optional[bool] = None
    parent_id: Optional[int] = Field(default=None, foreign_key="hackernewsitem.id")
    poll: Optional[int] = None
    kids: list["HackerNewsItem"] = Relationship(
        sa_relationship_kwargs=dict(
            backref=backref("parent", remote_side="HackerNewsItem.id"),
        ),
    )
    url: Optional[str] = None
    score: Optional[int] = None
    title: Optional[str] = None
    descendants: Optional[int] = None
