# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Optional, List
from contextlib import AsyncExitStack
import botocore.exceptions

from amazon_sagemaker_sql_execution.models.sql_execution import SQLExecutionRequest
from amazon_sagemaker_sql_execution.utils.sql_connection_factory import SQLConnectionFactory
from amazon_sagemaker_sql_execution.exceptions import (
    SQLExecutionError,
    ConnectionCreationError,
)
from amazon_sagemaker_sql_execution.exceptions import (
    SecretsRetrieverError,
)

from amazon_sagemaker_sql_editor.utils.client_factory import ClientFactory
from amazon_sagemaker_sql_editor.utils.constants import ClientType, NodeType
from amazon_sagemaker_sql_editor.utils.sql_execution import SQLExecutionClient

from amazon_sagemaker_sql_editor.utils.async_io import async_wrap

from amazon_sagemaker_sql_editor.utils.exceptions import (
    SagemakerSQLDataProviderServiceFault,
    SagemakerSQLDataProviderServiceError,
    SagemakerSQLFault,
    SagemakerSQLError,
)


class BaseDataProviderService:
    """
    Base class to create data-store clients and fetch data
    """

    def __init__(self, connection_name: str, path_components: List[str], metastore_type: str):
        """
        :param connection_name: Glue connection name
        :param path_components: List of components of the 'path' of nodes to be fetched
        :param metastore_type: Type of metastore for fetching connection details
        """
        self.connection_name = connection_name
        self.path_components = path_components
        self.metastore_type = metastore_type

    async def _initialize_client(self):
        raise NotImplementedError()

    async def _clean_up(self):
        pass

    async def _get_databases(self, **kwargs):
        raise NotImplementedError()

    async def _get_schemas(self, **kwargs):
        raise NotImplementedError()

    async def _get_data_catalogs(self, **kwargs):
        raise NotImplementedError()

    async def _get_tables(self, **kwargs):
        raise NotImplementedError()

    async def _get_columns(self, **kwargs):
        raise NotImplementedError()

    async def _get_data_at_path(self) -> dict:
        """
        1. Determines data hierarchy depth using self.path_components
        2. Calls relevant method to fetch data based on data hierarchy depth
        3. Returns fetched data in a standard format
        :return:
        """
        raise NotImplementedError()

    async def get_data_at_path(self) -> dict:
        raise NotImplementedError()


class SQLDataProviderService(BaseDataProviderService):
    """
    Class to create sql-based data-store clients and fetch data
    """

    def __init__(self, connection_name: str, path_components: List[str], metastore_type: str):
        super().__init__(
            connection_name=connection_name,
            path_components=path_components,
            metastore_type=metastore_type,
        )
        self.service_client: Optional[SQLExecutionClient] = None
        self.service_client_args = {
            "metastore_type": self.metastore_type,
            "metastore_id": self.connection_name,
        }

    async def _initialize_client(self):
        # TODO: Error handling
        async with ClientFactory().create_client(
            ClientType.SQL, self.service_client_args
        ) as client:
            self.service_client = client

    async def _get_query_results(self, sql_query: str):
        # create connection
        connection = await async_wrap(SQLConnectionFactory.create_connection)(
            metastore_id=self.service_client.metastore_id,
            metastore_type=self.service_client.metastore_type,
            connection_parameters={},
        )

        # create sql query request
        execution_request = SQLExecutionRequest(sql_query, query_params={})

        # execute query
        sql_exec_response = await async_wrap(connection.execute)(execution_request)

        # close connection
        connection.close()

        # return response
        return sql_exec_response.data

    async def get_data_at_path(self) -> dict:
        # TODO: update query in baseclasses to pull data using the format `SELECT col1, col2 ..` to
        #  always receive columns in predictable order.
        try:
            await self._initialize_client()
            data = await self._get_data_at_path()
            await self._clean_up()
            return data
        except SecretsRetrieverError as e:
            raise SagemakerSQLError(e)
        except (SQLExecutionError, ConnectionCreationError) as error:
            raise SagemakerSQLDataProviderServiceError(error)
        except Exception as e:
            raise SagemakerSQLDataProviderServiceFault(e)


class BotoDataProviderService(BaseDataProviderService):
    """
    Class to create boto-based data-store clients and fetch data
    """

    def __init__(self, connection_name: str, path_components: List[str], metastore_type: str):
        super().__init__(
            connection_name=connection_name,
            path_components=path_components,
            metastore_type=metastore_type,
        )
        self.service_client = None
        self.service_client_args = {}
        self.service_client_fault_codes = []
        self.service_client_error_codes = []

        self._exit_stack = AsyncExitStack()

    async def __aenter__(self):
        self.service_client = await self._exit_stack.enter_async_context(
            ClientFactory().create_client(ClientType.BOTO, self.service_client_args)
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    async def _initialize_client(self):
        await self.__aenter__()

    async def _clean_up(self):
        await self.service_client.close()

    async def get_data_at_path(self) -> dict:
        try:
            await self._initialize_client()
            data = await self._get_data_at_path()
            await self._clean_up()
            return data
        except botocore.exceptions.EndpointConnectionError as e:
            # TODO: exact error message to be updated after PM sign off.
            raise ConnectionError(
                "{}. Please check your network settings or contact support for assistance.".format(
                    str(e)
                )
            )
        except botocore.exceptions.ClientError as error:
            boto_error_code = error.response["Error"]["Code"]
            if boto_error_code in self.service_client_fault_codes:
                raise SagemakerSQLDataProviderServiceFault(error)
            elif boto_error_code in self.service_client_error_codes:
                raise SagemakerSQLDataProviderServiceError(error)
            else:  # Mark all unknown exceptions as faults for the sake of caution
                raise SagemakerSQLFault(error)
