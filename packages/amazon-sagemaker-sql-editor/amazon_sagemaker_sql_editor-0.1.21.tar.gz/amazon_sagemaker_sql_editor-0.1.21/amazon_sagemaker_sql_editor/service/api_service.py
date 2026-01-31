# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import asyncio
import json
from logging import Logger
from typing import Tuple

from http import HTTPStatus

from tornado.ioloop import IOLoop

from amazon_sagemaker_sql_execution.utils.metrics.service_metrics import (
    InstanceAttributeMetricsContextMixin,
    ClassAttributeMetricsContextMixin,
)
from amazon_sagemaker_sql_editor.cache.api_cache import PostDataSourcesApiCache
from amazon_sagemaker_sql_editor.model.models import GlueConnectionModel
from amazon_sagemaker_sql_editor.utils.client_factory import ClientFactory
from amazon_sagemaker_sql_editor.utils.constants import (
    ClientType,
    DataSourceType,
    PathEnum,
    DataSourcesApiResponse,
    AutocompleteApiConstants,
)
from amazon_sagemaker_sql_editor.adapter.adapter_factory import (
    GetConnectionsResponseAdapterFactory,
    PostDataSourcesResponseAdapterFactory,
)
from amazon_sagemaker_sql_editor.service.service_factory import (
    DataProviderServiceFactory,
)
from amazon_sagemaker_sql_editor.utils.language_server.autocomplete_schema_adapter import (
    AutocompleteSchemaAdapter,
)
from amazon_sagemaker_sql_editor.utils.language_server.autocomplete_file_handler import (
    AutocompleteSchemaFileHandler,
)
from amazon_sagemaker_sql_editor.utils.pagination.paginator import Paginator
from amazon_sagemaker_sql_editor.utils.api_utils import PathHelper

from amazon_sagemaker_sql_editor.utils.exceptions import (
    SagemakerSQLApiServiceError,
    SagemakerSQLApiServiceFault,
    SagemakerSQLFault,
    SagemakerSQLError,
    SageMakerSQLExceptionFactory,
)
from amazon_sagemaker_sql_editor.utils.metrics.service_metrics import (
    async_add_metrics,
)


# TODO: Alternate approach to consider: we are instantiating new Service to handle each request.
#  Based on the name a Service can be a single instance which processes all the requests.


class GetConnectionsApiService(InstanceAttributeMetricsContextMixin):
    """
    Class to call downstream clients and formulate server response for api: GET./api/connections
    """

    def __init__(self):
        super().__init__()

    @async_add_metrics("GetConnectionsApi")
    async def get_response(
        self,
        connection_filter_type: str = None,
        connection_filter_source: str = None,
        enable_default_athena: bool = None,
    ) -> dict:
        """
        Returns server response as dict

        :param connection_filter_type: type to filter connections on
        :param connection_filter_source: source to filter connections on
        :param enable_default_athena: decides whether default athena connection should be returned
        :return:
        """

        # create boto client
        client_factory = ClientFactory()
        glue_client_args = {"service_name": "glue"}
        async with client_factory.create_client(ClientType.BOTO, glue_client_args) as glue_client:
            # TODO: Update code to factor in 'connection_filter_source' i.e. GLUE_CONNECTION, GLUE_DATA_CATALOG etc.
            # get glue connections
            try:
                glue_connections = await glue_client.get_connections()
            except Exception as error:
                raise SageMakerSQLExceptionFactory.get_sql_exception(error)

            # create adapter instance
            connections_response_adapter = GetConnectionsResponseAdapterFactory().get_adapter(
                DataSourceType.GLUE
            )
            connections_response_adapter = connections_response_adapter(
                connections=glue_connections, enable_default_athena=enable_default_athena
            )

            # filter connections
            if connection_filter_type:
                connections_response_adapter.filter_response(connection_filter_type)

            # convert model for server response
            response = connections_response_adapter.convert_model_to_dict()
            return response


class PostDataSourcesApiService(InstanceAttributeMetricsContextMixin):
    """
    Class to call downstream clients and formulate server response for api: POST./api/data-sources
    """

    def __init__(self):
        # PostDataSourcesApiCache instance to manage cached server response
        super().__init__()
        self.acache = PostDataSourcesApiCache()

    @async_add_metrics("PostDataSourcesApi")
    async def get_response(
        self,
        path: str,
        refresh: bool = False,
        modified_since: float = None,
        next_token: str = None,
        page_size: int = None,
        enable_default_athena: bool = None,
    ) -> Tuple[bool, dict]:
        """
        1. Invalidates cache based on 'refresh' flag
        2. Fetches the entire data from downstream APIs (or cache if available)
        3. Slices the data for pagination
        4. Uses if_modified_since to set a modified flag as return value
        5. Returns paginated response

        :param path: path at which nodes' data needs to be fetched. "/" separated str value
        :param refresh: boolean value determining whether to invalidate cache
        :param modified_since: datetime value to check if server response has been modified since given time
        :param next_token: pagination token to determine the next set of page data
        :param page_size: page size of the response to be returned
        :param enable_default_athena: decides whether default athena connection should be returned
        :return: tuple[bool, dict]: 2-tuple with 1st element as if_modified_since and 2nd element as server response
        """
        if refresh and next_token is not None:
            raise SagemakerSQLApiServiceError(
                "Invalid request. 'next_token' should be None when 'refresh' = True"
            )

        # fetch entire data from data-stores APIs or cache (if available). For most client requests (per user), this
        # data will be fetched from cache. We fetch all the data at once and then paginate subsequently.
        # This saves us multiple network calls and improves latency.
        response = await self.acache.get_response_memoized(
            self._get_response,
            path=path,
            refresh=refresh,
            enable_default_athena=enable_default_athena,
        )

        if refresh:
            # invalidate cache for nodes under path
            self.acache.delete_cache_for_children_nodes(path)

        # set default page size if not provided
        page_size = 20 if page_size is None else page_size
        # paginate the response if page_size > 0, else return the entire data
        # TODO: Revisit logic once UI layer starts supporting pagination
        if page_size > 0:
            next_token, node_list = Paginator().next_page(
                token=next_token,
                data=response[DataSourcesApiResponse.NODE_LIST_KEY],
                page_size=page_size,
            )
            response[DataSourcesApiResponse.NODE_LIST_KEY] = node_list

        # check for if-modified-since
        modified = True
        if modified_since:
            modified = response[DataSourcesApiResponse.LAST_UPDATE_TIME_KEY] > modified_since

        response = {**response, DataSourcesApiResponse.NEXT_TOKEN_KEY: next_token}
        return modified, response

    async def _get_datastore_type_from_cache(self, connection_name: str) -> str:
        """
        Gets the connection info from cache to return the datastore type

        :param connection_name: connection's name to pull the connection info
        :return: datastore type
        """
        # get connections under root node
        cached_connections = await self.acache.get_response_memoized(
            self._get_response, path=PathEnum.ROOT, refresh=False
        )

        for connection_info in cached_connections[DataSourcesApiResponse.NODE_LIST_KEY]:
            if connection_name == connection_info[DataSourcesApiResponse.NAME_KEY]:
                return connection_info[DataSourcesApiResponse.NODE_DATA_KEY][
                    DataSourcesApiResponse.TYPE_KEY
                ]

        # if the code flow reached here, 'connection_name' was not found in cache.
        raise SagemakerSQLApiServiceError(f'connection name "{connection_name}" does not exist!')

    async def _get_response(self, path: str, enable_default_athena: bool) -> dict:
        """
        Returns nodes' data at path as dict

        :param path: path at which nodes' data needs to be fetched. "/" separated str value
        :return:
        """

        # parse path
        is_root = PathHelper.is_root_path(path)
        path_components = PathHelper.get_path_components(path)

        # return all data sources
        # create boto client
        glue_client_args = {"service_name": "glue"}
        # TODO Update code to factor in multiple connection sources i.e. GLUE_CONNECTION, GLUE_DATA_CATALOG etc.
        async with ClientFactory().create_client(ClientType.BOTO, glue_client_args) as glue_client:
            if is_root:
                # get glue connections
                self.metrics_context.set_property("ConnectionType", "GLUE")
                try:
                    glue_connections = await glue_client.get_connections()
                except Exception as error:
                    raise SageMakerSQLExceptionFactory.get_sql_exception(error)

                # initialize adapter
                data_sources_response_adapter = PostDataSourcesResponseAdapterFactory().get_adapter(
                    DataSourceType.GLUE.value.__str__()
                )
                data_sources_response_adapter = data_sources_response_adapter(
                    connections=glue_connections, enable_default_athena=enable_default_athena
                )

                # send server response
                response = data_sources_response_adapter.convert_model_to_dict()
            else:
                # get connection metadata; determine data-store
                connection_name = path_components[0].strip()
                # get the datastore type to select the relevant datastore for retrieving database/schema entities
                data_store_type = await self._get_datastore_type_from_cache(connection_name)
                self.metrics_context.set_property("ConnectionType", data_store_type)
                # fetch data from data provider service
                data_provider_service = DataProviderServiceFactory().create_service(
                    data_provider_type=data_store_type
                )
                data_provider_service = data_provider_service(
                    connection_name=connection_name,
                    path_components=path_components,
                    metastore_type="GLUE_CONNECTION",
                )
                data_at_path = await data_provider_service.get_data_at_path()

                # initialize adapter instance
                data_source_response_adapter = PostDataSourcesResponseAdapterFactory().get_adapter(
                    data_store_type
                )
                data_source_response_adapter = data_source_response_adapter(**data_at_path)

                # send server response
                response = data_source_response_adapter.convert_model_to_dict()

            return response


class PostDataSourcesAutocompleteApiService(ClassAttributeMetricsContextMixin):
    """
    Singleton class providing capabilities to create and manage server responses for the API: POST./api/data-sources-autocomplete.
    Singleton nature is required for the API to exhibit short-polling capabilities.

    Class is responsible to fetch the entire schema of a connection and storing it as schema files in pre-defined format.
    The files are used to parse the schema by sql-language-sever for serving autocomplete suggestions.

    Broadly, server response codes are explained below:

    202 - task to fetch connection schema in progress
    200 - connection schema fetching is complete
    5xx/4xx - error while fetching connection schema

    NOTE: server expects only a single connection being polled by the client at a time. Server assumes that the
    connection being polled for is the most recently active connection by the client.
    """

    _instance = None
    log = None

    # for acquiring async-safe locks
    # note: it doesn't guarantee thread-safety.
    # reference: https://docs.python.org/3/library/asyncio-sync.html
    instance_lock = asyncio.Lock()
    connection_mutex_lock = asyncio.Lock()

    # each connection's status is maintained as a dict in the following format:
    #   {
    #     "my-connection": "IN_PROGRESS|ERROR"
    #   }
    #
    # connection persists in the dict only for the duration of server's long-running task to fetching the entire schema
    connection_fetch_status = {}

    # PostDataSourcesApiService instance to call methods for fetching data from underlying data-sources
    data_sources_api_service = PostDataSourcesApiService()

    # to maintain the id of last connection which requested the server for the API: POST./api/data-sources-autocomplete.
    last_active_connection = None

    def __new__(cls, *args, **kwargs):
        # if instance is None, create and store new instance
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        # return the stored instance
        return cls._instance

    @classmethod
    async def get_instance(cls, log: Logger = None):
        # acquire lock for asyncio-tasks
        async with cls.instance_lock:
            instance = cls.__new__(cls)

            log = Logger(name="AutocompleteApiServiceLogger") if log is None else log
            instance.log = log

            return instance

    async def _update_connection_status(self, connection_name: str, status: str):
        async with PostDataSourcesAutocompleteApiService.connection_mutex_lock:
            self.connection_fetch_status[connection_name] = status

    async def _reset_central_schema(self, connection_name: str):
        async with PostDataSourcesAutocompleteApiService.connection_mutex_lock:
            # empty content of central schema file if active connection has changed
            if connection_name != self.last_active_connection:
                AutocompleteSchemaFileHandler.update_central_schema_file(connection_name=None)

    async def _update_last_active_connection(self, connection_name: str):
        async with PostDataSourcesAutocompleteApiService.connection_mutex_lock:
            self.last_active_connection = connection_name

    async def _remove_connection(self, connection_name: str):
        async with PostDataSourcesAutocompleteApiService.connection_mutex_lock:
            if connection_name in self.connection_fetch_status:
                del self.connection_fetch_status[connection_name]

    async def _get_connection_status(self, connection_name: str):
        async with PostDataSourcesAutocompleteApiService.connection_mutex_lock:
            return self.connection_fetch_status.get(connection_name, None)

    @async_add_metrics("PostDataSourcesAutocompleteApi")
    async def get_response(self, connection_name: str):
        """
        Method to initiate a non-awaited async process to fetch and store a connection's information schema and send back
        appropriate server response. This method handles client polling.

        :param connection_name: connection name for which information schema is to be fetched
        :return:
        """

        # reset language-server central schema file (if required)
        await self._reset_central_schema(connection_name)

        # update last active connection
        await self._update_last_active_connection(connection_name)

        # retrieve connection status
        connection_status = await self._get_connection_status(connection_name)

        # if connection in progress:
        if connection_status == AutocompleteApiConstants.CONNECTION_STATUS_IN_PROGRESS:
            self.log.info(
                "schema-fetching process for connection %s is in progress",
                connection_name,
            )
            # send response 202
            return HTTPStatus.ACCEPTED.real
        # if connection in server-error state
        elif connection_status == AutocompleteApiConstants.CONNECTION_STATUS_SERVER_ERROR:
            self.log.info(
                f"schema-fetching process for connection %s in server-error state",
                connection_name,
            )
            # remove connection from memory
            await self._remove_connection(connection_name)

            # send response error code
            return HTTPStatus.INTERNAL_SERVER_ERROR.real
        # if connection in client-error state
        elif connection_status == AutocompleteApiConstants.CONNECTION_STATUS_CLIENT_ERROR:
            self.log.info(
                "schema-fetching process for connection %s in client-error state",
                connection_name,
            )
            # remove connection from memory
            await self._remove_connection(connection_name)

            # send response error code
            return HTTPStatus.BAD_REQUEST.real
        # if connection not in memory:
        elif connection_status is None:
            self.log.info(
                "connection %s not found in memory. Checking connection schema state from file",
                connection_name,
            )

            # if connection schema file is updated i.e. synced with server cache
            if await self.is_connection_updated(connection_name):
                self.log.info("connection %s schema is in-sync with server cache", connection_name)

                # update central schema file
                AutocompleteSchemaFileHandler.update_central_schema_file(connection_name)

                # send response 200
                return HTTPStatus.OK.real
            # if connection schema file is NOT updated i.e. NOT synced with server cache
            else:
                self.log.info("connection %s schema is in-sync with server cache", connection_name)
                # start new non-awaited async process to update schema
                IOLoop.current().spawn_callback(
                    self.initiate_get_data_for_all_levels, connection_name
                )

                # send response 202
                return HTTPStatus.ACCEPTED.real
        # if unknown connection status
        else:
            raise SagemakerSQLFault(
                f"Unknown status {connection_status} for connection in memory: {connection_name}"
            )

    async def is_connection_updated(self, connection_name) -> bool:
        """
        Retrieves connection level information from the API POST./api/data-sources and
        checks if the that connection's schema stored on file is in sync with the one available from the API.

        :param connection_name: name of the connection to check
        :return bool: returns false if the connection schema on file is stale.
        """
        modified, response = await self.data_sources_api_service.get_response(
            path=connection_name, page_size=-1
        )
        return AutocompleteSchemaFileHandler.is_connection_schema_file_updated(
            connection_name=connection_name,
            last_modified=response[DataSourcesApiResponse.LAST_UPDATE_TIME_KEY],
        )

    async def initiate_get_data_for_all_levels(self, connection_name) -> None:
        """
        Method to fetch the entire information schema under a particular connection and update connection level
        schema files for sql-language-server.

        :param connection_name: connection name to fetch the information schema under
        """
        self.log.info(
            "async task spawned to fetch entire schema for connection %s",
            connection_name,
        )

        # add connection in memory as 'in_progress'
        await self._update_connection_status(
            connection_name=connection_name,
            status=AutocompleteApiConstants.CONNECTION_STATUS_IN_PROGRESS,
        )

        try:
            # get data for all levels
            response = await self._get_data_for_all_levels(path=connection_name)

            # adapt to sql-language-server compatible format
            connection_schema = AutocompleteSchemaAdapter.adapt_to_language_server_format(response)

            # update connection-level language-server file
            AutocompleteSchemaFileHandler.update_connection_schema_file(
                connection_name=connection_name, connection_schema=connection_schema
            )

            self.log.info(
                "async task to fetch entire schema completed for connection %s",
                connection_name,
            )

            # remove connection from memory
            await self._remove_connection(connection_name=connection_name)
        except SagemakerSQLFault as e:
            self.log.error(e)
            # update connection status in memory as 'error'
            await self._update_connection_status(
                connection_name=connection_name,
                status=AutocompleteApiConstants.CONNECTION_STATUS_SERVER_ERROR,
            )
        except SagemakerSQLError as e:
            self.log.error(e)
            # update connection status in memory as 'error'
            await self._update_connection_status(
                connection_name=connection_name,
                status=AutocompleteApiConstants.CONNECTION_STATUS_CLIENT_ERROR,
            )

    async def _get_data_for_all_levels(self, path: str):
        """
        Method to create the entire information schema under a particular path as tree representation.
        - Makes recursive calls to 'class PostDataSourcesApiService -> get_response()' method for fetching data node-level by node-level.
        - Implements a batching system to parallelize API calls at a node-level (upto a threshold)

        :param path: node path under which schema is to be fetched
        :return: information schema
        """
        # page_size = -1 to skip paginating the responses
        modified, response = await self.data_sources_api_service.get_response(
            path=path, page_size=-1
        )

        response_node_list = response[DataSourcesApiResponse.NODE_LIST_KEY]
        all_responses = []
        if response_node_list:
            batch_size = 5  # value for batch size is heuristically chosen
            batch_requests = []

            for i, node in enumerate(response_node_list):
                if not node[DataSourcesApiResponse.IS_LEAF_KEY]:
                    # create node path
                    if PathHelper.is_root_path(path):
                        node_path = f"{path}{node[DataSourcesApiResponse.NAME_KEY]}"
                    else:
                        node_path = (
                            f"{path}{PathEnum.DELIMITER}{node[DataSourcesApiResponse.NAME_KEY]}"
                        )

                    # append tasks to list to create a batch
                    loop = asyncio.get_running_loop()
                    batch_requests.append(
                        loop.create_task(self._get_data_for_all_levels(path=node_path))
                    )

                if (i + 1) % batch_size == 0 or (i + 1) == len(response_node_list):
                    # either the batch size limit or the node children limit reached, 'await' till the batch completes
                    # processing. this is done to avoid throttling issues from the underlying data-source's end as well
                    # as to avoid overloading server capacity.
                    batch_responses = await asyncio.gather(*batch_requests)
                    # accumulate responses from all batches
                    all_responses.extend(batch_responses)
                    # reset batch list
                    batch_requests = []

            # set parent node's list of children
            for i, node in enumerate(all_responses):
                response_node_list[i][DataSourcesApiResponse.NODE_LIST_KEY] = node[
                    DataSourcesApiResponse.NODE_LIST_KEY
                ]

        return response


class CreateConnectionApiService(InstanceAttributeMetricsContextMixin):
    def __init__(self):
        super().__init__()

    @async_add_metrics("CreateConnectionApi")
    async def create_connection(
        self,
        name: str,
        description: str,
        connection_type: str,
        connection_properties: str,
        current_user: str,
    ):
        # create boto client
        client_factory = ClientFactory()
        glue_client_args = {"service_name": "glue"}
        async with client_factory.create_client(ClientType.BOTO, glue_client_args) as glue_client:
            try:
                # Get region from client factory
                region = client_factory._get_region()

                return await glue_client.create_connection(
                    ConnectionInput={
                        "Name": name,
                        "Description": description,
                        "ConnectionType": connection_type,
                        "ConnectionProperties": clean_python_connection_properties(
                            connection_properties, region
                        ),
                    },
                    Tags={
                        "UserProfile": current_user,
                        "AppType": "JL",
                    },
                )
            except Exception as error:
                raise SageMakerSQLExceptionFactory.get_sql_exception(error)


class UpdateConnectionApiService(InstanceAttributeMetricsContextMixin):
    def __init__(self):
        super().__init__()

    @async_add_metrics("UpdateConnectionApi")
    async def update_connection(
        self,
        old_name: str,
        new_name: str,
        description: str,
        connection_type: str,
        connection_properties: str,
    ):
        # create boto client
        client_factory = ClientFactory()
        glue_client_args = {"service_name": "glue"}
        async with client_factory.create_client(ClientType.BOTO, glue_client_args) as glue_client:
            try:
                # Get region from client factory
                region = client_factory._get_region()

                return await glue_client.update_connection(
                    Name=old_name,
                    ConnectionInput={
                        "Name": new_name,
                        "Description": description,
                        "ConnectionType": connection_type,
                        "ConnectionProperties": clean_python_connection_properties(
                            connection_properties, region
                        ),
                    },
                )
            except Exception as error:
                raise SageMakerSQLExceptionFactory.get_sql_exception(error)


class DeleteConnectionApiService(InstanceAttributeMetricsContextMixin):
    def __init__(self):
        super().__init__()

    @async_add_metrics("DeleteConnectionApi")
    async def delete_connection(self, name: str):
        # create boto client
        client_factory = ClientFactory()
        glue_client_args = {"service_name": "glue"}
        async with client_factory.create_client(ClientType.BOTO, glue_client_args) as glue_client:
            try:
                return await glue_client.delete_connection(ConnectionName=name)
            except Exception as error:
                raise SageMakerSQLExceptionFactory.get_sql_exception(error)


class GetConnectionApiService(InstanceAttributeMetricsContextMixin):
    def __init__(self):
        super().__init__()

    @async_add_metrics("GetConnectionApi")
    async def get_connection(self, connection_name: str):
        # create boto client
        client_factory = ClientFactory()
        glue_client_args = {"service_name": "glue"}
        async with client_factory.create_client(ClientType.BOTO, glue_client_args) as glue_client:
            try:
                connection = await glue_client.get_connection(Name=connection_name)
                return GlueConnectionModel(
                    name=connection["Connection"]["Name"],
                    description=connection["Connection"]["Description"],
                    connectionType=connection["Connection"]["ConnectionType"],
                    connectionProperties=connection["Connection"]["ConnectionProperties"],
                    lastUpdateTime=connection["Connection"]["LastUpdatedTime"].timestamp(),
                )
            except Exception as error:
                raise SageMakerSQLExceptionFactory.get_sql_exception(error)


def clean_python_connection_properties(properties: dict, region: str = None):
    clean_properties = {}
    for property_key in properties:
        if property_key == "PythonProperties":
            clean_python_properties = {}
            python_properties = json.loads(properties[property_key])

            # Construct host for Redshift Serverless if serverless parameters are provided
            if (
                region
                and "serverless_work_group" in python_properties
                and python_properties["serverless_work_group"]
                and "serverless_acct_id" in python_properties
                and python_properties["serverless_acct_id"]
                and "host" not in python_properties
            ):
                python_properties["host"] = (
                    f"{python_properties['serverless_work_group']}."
                    f"{python_properties['serverless_acct_id']}."
                    f"{region}.redshift-serverless.amazonaws.com"
                )

            for python_property_key in python_properties:
                if python_properties[python_property_key]:
                    clean_python_properties[python_property_key] = python_properties[
                        python_property_key
                    ]
            clean_properties[property_key] = json.dumps(clean_python_properties)
        else:
            clean_properties[property_key] = properties[property_key]
    return clean_properties
