class CacheSourceNonInitError(Exception):
    def __init__(self):
        super().__init__('指定的缓存源未初始化')


class CacheSourceNotSupportError(Exception):
    def __init__(self, cache_source: str):
        super().__init__(f'指定的缓存源 {cache_source} 不支持')


class ApiRequestError(Exception):
    def __init__(self, errmsg: str):
        super().__init__(f'API 请求错误，错误信息 {errmsg}')
