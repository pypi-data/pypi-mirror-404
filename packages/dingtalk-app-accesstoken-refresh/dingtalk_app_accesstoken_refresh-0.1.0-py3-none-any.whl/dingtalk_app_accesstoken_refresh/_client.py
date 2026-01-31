from contextlib import contextmanager

import requests
from tinydb import TinyDB

from . import _constants, _errors
from ._cache_source.local_cache import LocalCache
from ._types import AppAccessToken


class DingTalkAppAccessTokenRefreshClient:
    def __init__(self):
        self._local_source = None

    def _get_cache_source(self, cache_source: _constants.CacheSource):
        """
        获取缓存源对象

        Args:
            cache_source (CacheSource): 缓存源
        Returns:
            缓存源对象
        Raises:
            CacheSourceNotSupportError: 缓存源不支持
        """

        cache_source_obj = None
        match cache_source:
            case _constants.CacheSource.LOCAL:
                cache_source_obj = self._local_source
                cache_source_obj.connect()
            case _:
                raise _errors.CacheSourceNotSupportError

        if not cache_source_obj:
            raise _errors.CacheSourceNonInitError

        return cache_source_obj

    def _get_app_access_token_from_api(self, client_id: str, client_secret: str):
        """
        从 API 获取应用 AccessToken

        Args:
            client_id (str): 钉钉应用 client_id
            client_secret (str): 钉钉应用 client_secret
        Returns:
            应用 AccessToken 对象
        """

        payload = {'appKey': client_id, 'appSecret': client_secret}
        resp = requests.post(
            'https://api.dingtalk.com/v1.0/oauth2/accessToken', json=payload
        )
        resp_jsonify: dict = resp.json()
        if resp.status_code != 200:
            raise _errors.ApiRequestError(errmsg=resp_jsonify.get('message'))

        return AppAccessToken(
            client_id=client_id,
            access_token=resp_jsonify.get('accessToken'),
            expire_in=resp_jsonify.get('expireIn'),
        )

    def enable_local_cache(
        self,
        cache_file_path: str,
        custom_cache_name: str = None,
        tinydb_ins: TinyDB = None,
    ):
        """
        启用本地缓存

        Args:
            cache_file_path (str): 缓存文件路径
            custom_cache_name (str): 自定义缓存表名
            tinydb_ins (TinyDB): TinyDB实例
        """

        if self._local_source is not None:
            return

        self._local_source = LocalCache(
            file_path=cache_file_path,
            table_name=custom_cache_name,
            tinydb_ins=tinydb_ins,
        )

    @contextmanager
    def get_access_token(
        self,
        client_id: str,
        client_secret: str,
        cache_source: _constants.CacheSource = None,
    ):
        """
        获取钉钉应用 access_token

        Args:
            client_id (str): 钉钉应用 client_id
            client_secret (str): 钉钉应用 client_secret
            cache_source (CacheSource): 缓存源, 留空则不读取缓存通过 API 获取
        Returns:
            应用 AccessToken 对象
        Raises:
            CacheSourceNotSupportError: 缓存源不支持
            CacheSourceNonInitError: 缓存源未初始化
        """

        cache_app_access_token = None
        app_access_token = None
        cache_source_obj = None

        try:
            if cache_source and isinstance(cache_source, _constants.CacheSource):
                cache_source_obj = self._get_cache_source(cache_source=cache_source)

            if cache_source_obj:
                cache_app_access_token = cache_source_obj.get_access_token(
                    client_id=client_id
                )

            if not cache_app_access_token or cache_app_access_token.is_expired:
                app_access_token = self._get_app_access_token_from_api(
                    client_id=client_id, client_secret=client_secret
                )

            if app_access_token and cache_source_obj:
                if cache_app_access_token:
                    cache_source_obj.update_access_token(app_access_token)
                else:
                    cache_source_obj.insert_access_token(app_access_token)
            yield app_access_token if app_access_token else cache_app_access_token
        except Exception as e:
            raise e
        finally:
            if cache_source_obj:
                cache_source_obj.close()
