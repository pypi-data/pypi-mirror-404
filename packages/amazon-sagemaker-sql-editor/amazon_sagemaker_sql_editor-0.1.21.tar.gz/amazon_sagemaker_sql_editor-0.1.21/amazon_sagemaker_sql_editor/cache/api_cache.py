# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os.path
from pathlib import Path

from diskcache import Cache
from diskcache.core import ENOVAL, args_to_key
from diskcache.core import Disk

from amazon_sagemaker_sql_editor.utils.exceptions import SagemakerSQLFault
from amazon_sagemaker_sql_editor.utils.constants import (
    CacheLocation,
    PathEnum,
    Api,
    DataSourcesApiResponse,
)
from amazon_sagemaker_sql_editor.utils.api_utils import PathHelper, SageMakerUtils


class PostDataSourcesApiCache(Cache):
    """
    Helper class to provide async compatible caching functions for POST./api/data-sources.
    Caching is done for each node-level for the right-panel data view.
    """

    def __init__(self, directory=None, timeout=60, disk=Disk, **settings):
        """
        :param directory: directory to save cache database in
        :param timeout: cache db connection timeout
        :param disk: diskcache Disk type or subclass for serialization
        :param settings: any of diskcache DEFAULT_SETTINGS
        """
        if directory is None:
            directory = self._determine_cache_directory_path()

        # set max cache size to 100 MB to limit memory footprint on disk
        settings["size_limit"] = 100 * (2**20)
        super().__init__(directory=directory, timeout=timeout, disk=disk, **settings)

    def _create_dirs(self, fully_qualified_directory_path):
        # Specify the directory paths
        Path(fully_qualified_directory_path).mkdir(parents=True, exist_ok=True)

    def _determine_cache_directory_path(self):
        if SageMakerUtils.is_sagemaker_environment():
            return os.path.join(CacheLocation.SAGEMAKER_PARENT_DIR, CacheLocation.API_SUB_DIR)
        else:
            return os.path.join(CacheLocation.LOCAL_PARENT_DIR, CacheLocation.API_SUB_DIR)

    def _invalidate_path_children(self, path: str):
        """
        Function which clears all cache items which are children of path
        """
        if path == PathEnum.ROOT:
            raise SagemakerSQLFault(f"path cannot be root")

        path = f"{path}{PathEnum.DELIMITER}"
        for key in self.iterkeys():
            for key_item in key:
                if type(key_item) == str and key_item.startswith(path):
                    self.delete(key)

    def _invalidate_root_path_children(self):
        """
        Function which clears all cache items except at root path
        """
        # get root cache value
        root_cache_key = self.__cache_key__(ignore=set(), path=PathEnum.ROOT)
        root_cache_val = self.get(root_cache_key, default=ENOVAL, retry=True)

        # clear everything
        self.clear(retry=True)

        # set root cache value again
        if root_cache_val is not ENOVAL:
            self.set(root_cache_key, root_cache_val, expire=None, tag=None, retry=True)

    def delete_cache_for_children_nodes(self, path: str):
        """
        Deletes cache for nodes which are children of path

        :param path: the path of nodes below which cache deletion needs to happen
        """
        is_root = PathHelper.is_root_path(path)
        # Note: with transact(retry=True), diskcache performs infinite retries whenever an internal sqlite timeout
        # exception occurs while performing CRUD operation with cache keys.
        with self.transact(retry=True):  # Perform operations on keys atomically
            if is_root:  # if root node, clear all children under root
                self._invalidate_root_path_children()
            else:  # if non-root node, clear cache for only the children paths
                self._invalidate_path_children(path=path)

    def _set_last_update_time_for_parent_nodes(self, path: str, last_update_time: float) -> None:
        """
        Update 'lastUpdateTime' for all cached nodes above path

        :param path: path for which above nodes are to be updated
        :param last_update_time: value to update
        """
        # Note: with transact(retry=True), diskcache performs infinite retries whenever an internal sqlite timeout
        # exception occurs while performing CRUD operation with cache keys.
        with self.transact(retry=True):  # Perform updation of keys atomically
            # start with root path i.e., path=''
            path_to_update = PathEnum.ROOT
            # iterate over all path components. E.g. for path='my-conn/my-db', iterate over ['', 'my-conn', 'my-db']
            for path_component in PathHelper.get_path_components(path):
                # update 'lastUpdateTime' in cache
                cache_key = self.__cache_key__(ignore=set(), path=path_to_update)
                key_value = self.get(cache_key, default=ENOVAL, retry=True)

                if key_value is not ENOVAL:
                    key_value[DataSourcesApiResponse.LAST_UPDATE_TIME_KEY] = last_update_time
                    self.set(cache_key, key_value, expire=None, tag=None, retry=True)

                # append path with tne next path component. E.g. path='my-conn' -> path='my-conn/my-db'
                if path_to_update == PathEnum.ROOT:
                    path_to_update = f"{path_to_update}{path_component}"
                else:
                    path_to_update = f"{path_to_update}{PathEnum.DELIMITER}{path_component}"

    @staticmethod
    def __cache_key__(ignore: set, path: str):
        """
        Create key for cache items using 'path'

        Cache keys are tuples with the following format:
        (API_NAME, 'path', PATH)

        Examples:
        ('/api/data-sources', 'path', '')
        ('/api/data-sources', 'path', 'my-redshift-connection')
        ('/api/data-sources', 'path', 'my-redshift-connection/my-database')

        :param ignore: positional or keyword args to remove from cache key creation.
        :param path: path parameter which identifies the response to be returned.
        """
        # cache key prefix
        base = (Api.NAME_DATA_SOURCES.value,)

        # If typed is set to True, function arguments of different types will be
        # cached separately. E.g., f(3) and f(3.0) will be treated as distinct calls with distinct results.
        typed = False

        # create and return cache key
        key = args_to_key(base=base, args=(), kwargs={"path": path}, typed=typed, ignore=ignore)
        return key

    async def get_response_memoized(
        self,
        get_response_func: callable,
        path: str,
        refresh: bool,
        enable_default_athena: bool = None,
    ):
        """
        Fetches response from cache or underlying data-stores
        Updates lastUpdateTime for all parent nodes of path
        Returns response

        :param get_response_func: get_response() from PostDataSourcesApiService
        :param path: path for which response needs to be fetched
        :param refresh: whether to force-fetch from underlying data-stores
        :param enable_default_athena: whether default athena connection should be returned
        :return: response from cache or underlying data-stores
        """
        # fetch data from cache or underlying data-stores
        response, from_cache = await self._get_response_memoized(
            get_response_func,
            path=path,
            refresh=refresh,
            enable_default_athena=enable_default_athena,
        )

        # update 'lastUpdateTime' for all parent nodes of path
        if not from_cache:
            self._set_last_update_time_for_parent_nodes(
                path=path,
                last_update_time=response[DataSourcesApiResponse.LAST_UPDATE_TIME_KEY],
            )

        # return response
        return response

    async def _get_response_memoized(
        self,
        get_response_func: callable,
        path: str,
        enable_default_athena: bool = None,
        expire: float = None,
        tag=None,
        ignore=None,
        refresh=False,
    ):
        """
        Memoizing function using cache.

        Implementation flow:
        1. Creates cache key and performs a cache lookup.
        2. If cache hit, returns result with a `from_cache=True` flag
        3. If cache miss, calls the `get_response_func`, sets the result in cache, and returns it with a `from_cache=False` flag

        Repeated calls with the same arguments will lookup result in cache and
        avoid function evaluation.

        When expire is set to zero, function results will not be set in the
        cache. Cache lookups still occur, however.

        When refresh is set to True, function evaluation will always occur.

        :param callable get_response_func: function to call and memoize
        :param str path: path for which response needs to be fetched
        :param float expire: seconds until arguments expire
            (default None, no expiry)
        :param str tag: text to associate with arguments (default None)
        :param set ignore: positional or keyword args to ignore (default ())
        :param bool refresh: indicates whether to call callable (default False)
        :return: 2-tuple - (response, from_cache)

        """
        if ignore is None:
            ignore = set()
        if not callable(get_response_func):
            raise SagemakerSQLFault("get_response_func needs to be callable")

        key = self.__cache_key__(ignore=ignore, path=path)
        from_cache = True
        result = self.get(key, default=ENOVAL, retry=True)

        # call func if refresh=True or cache is not set
        if refresh or result is ENOVAL:
            from_cache = False
            result = await get_response_func(path=path, enable_default_athena=enable_default_athena)
            if expire is None or expire > 0:
                self.set(key, result, expire, tag=tag, retry=True)

        return result, from_cache
