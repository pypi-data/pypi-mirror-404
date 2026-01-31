from tinydb import Query, TinyDB

from .._constants import CacheSource
from .._types import AppAccessToken
from .types import CacheSourceClass


class LocalCache(CacheSourceClass):
    table_name = 'dingtalk_app_access_token_refresh_cache'

    def __init__(
        self, file_path: str, table_name: str = None, tinydb_ins: TinyDB = None
    ):
        """
        初始化本地存储

        Args:
            file_path (str): 本地存储文件路径
            table_name (str): 缓存表名
            tinydb_ins (TinyDB): TinyDB实例
        """

        self.__tinydb_auto_close = True
        self._file_path = file_path
        self._tinydb = None

        if table_name and isinstance(table_name, str):
            self.table_name = table_name

        if tinydb_ins and isinstance(tinydb_ins, TinyDB):
            self._tinydb = tinydb_ins
            self.__tinydb_auto_close = False
        else:
            self.connect()

    def connect(self):
        """
        连接TinyDB实例
        """

        if self._tinydb is None:
            self._tinydb = TinyDB(self._file_path)

    def get_access_token(self, client_id: str) -> AppAccessToken | None:
        """
        获取缓存中的 access_token

        Args:
            client_id (str): 客户端ID
        Returns:
            缓存中的数据对象
        """

        table = self._tinydb.table(self.table_name)
        record = table.get(Query().client_id == client_id)

        return (
            AppAccessToken(**{**record, 'cache_source': CacheSource.LOCAL})
            if record
            else None
        )

    def insert_access_token(self, app_access_token: AppAccessToken):
        """
        向缓存中新增 access_token

        Args:
            app_access_token (AppAccessToken): 钉钉应用 AccessToken对象
        """

        table = self._tinydb.table(self.table_name)
        table.insert(app_access_token.__dict__)

    def update_access_token(self, app_access_token: AppAccessToken):
        """
        更新缓存中的 access_token

        Args:
            app_access_token (AppAccessToken): 钉钉应用 AccessToken对象
        """

        table = self._tinydb.table(self.table_name)
        table.update(
            app_access_token.__dict__, Query().client_id == app_access_token.client_id
        )

    def close(self):
        """
        关闭TinyDB实例
        """

        if self.__tinydb_auto_close:
            self._tinydb.close()
            self._tinydb = None
