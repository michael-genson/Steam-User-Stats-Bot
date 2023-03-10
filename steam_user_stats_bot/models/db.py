from datetime import datetime

from ._base import StatsBotBaseModel


class UserIn(StatsBotBaseModel):
    id: str
    steam_id_64: str | None = None
    steam_api_key: str | None = None


class User(UserIn):
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        orm_mode = True

    @property
    def is_setup(self):
        return all([self.steam_id_64, self.steam_api_key])
