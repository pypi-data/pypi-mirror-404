from abc import abstractmethod

from .._types import AppAccessToken


class CacheSourceClass:
    @abstractmethod
    def get_access_token(self, client_id: str) -> AppAccessToken | None: ...

    @abstractmethod
    def insert_access_token(self, app_access_token: AppAccessToken): ...

    @abstractmethod
    def update_access_token(self, app_access_token: AppAccessToken): ...

    @abstractmethod
    def close(self): ...
