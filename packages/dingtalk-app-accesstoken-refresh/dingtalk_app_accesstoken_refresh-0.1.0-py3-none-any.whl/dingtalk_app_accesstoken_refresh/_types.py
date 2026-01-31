from dataclasses import dataclass, fields
from time import time

from ._constants import CacheSource


class FilteredDataclass(type):
    def __call__(cls, *args, **kwargs):
        # 过滤kwargs中多余的键
        valid_fields = {f.name for f in fields(cls)}
        kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
        return super().__call__(*args, **kwargs)


@dataclass
class AppAccessToken(metaclass=FilteredDataclass):
    """
    钉钉开放平台应用 AccessToken
    """

    client_id: str | None = None
    access_token: str | None = None
    expire_in: int | None = None
    expire_timestamp: int | None = None
    is_expired: bool = False
    cache_source: CacheSource | None = None

    def __post_init__(self):
        if (
            not self.expire_timestamp
            and self.expire_in
            and isinstance(self.expire_in, int)
        ):
            self.expire_timestamp = int((time() + self.expire_in) * 1000)

        self.is_expired = int(time() * 1000) > self.expire_timestamp
