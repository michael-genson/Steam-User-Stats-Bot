from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from sqlalchemy import DateTime


class BaseMixins:
    """
    `self.update` method which directly passing arguments to the `__init__`
    """

    def update(self, *args, **kwarg):
        self.__init__(*args, **kwarg)


class StatsBotDBBase(DeclarativeBase, BaseMixins):
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserInDB(StatsBotDBBase):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(primary_key=True)
    steam_id_64: Mapped[str | None] = mapped_column(nullable=True)
    steam_api_key: Mapped[str | None] = mapped_column(nullable=True)
