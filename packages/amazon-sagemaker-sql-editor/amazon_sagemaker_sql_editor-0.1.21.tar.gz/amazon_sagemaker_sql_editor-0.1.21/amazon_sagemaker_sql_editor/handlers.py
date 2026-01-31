# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import dataclasses
import json
import re
import traceback
from typing import Optional, Awaitable
from http import HTTPStatus

import tornado
from tornado import web
from tornado.web import HTTPError
from jupyter_server.base.handlers import JupyterHandler
import botocore.exceptions

from amazon_sagemaker_sql_editor.service.api_service import (
    CreateConnectionApiService,
    DeleteConnectionApiService,
    GetConnectionApiService,
    GetConnectionsApiService,
    PostDataSourcesApiService,
    PostDataSourcesAutocompleteApiService,
    UpdateConnectionApiService,
)
from amazon_sagemaker_sql_editor.service.schema_service import SchemaManagerService
from amazon_sagemaker_sql_editor.service.search_service import (
    SearchService,
    SearchRequest,
)
from amazon_sagemaker_sql_editor.utils.constants import (
    Api,
    ConnectionsApiBodyArgs,
    ConnectionsApiQueryArgs,
    DataSourcesApiBodyArgs,
    DataSourcesApiHeaders,
    DataSourcesAutocompleteApiBodyArgs,
)
from amazon_sagemaker_sql_editor.utils.exceptions import (
    AccessDeniedError,
    DuplicateResourceException,
    InvalidInputException,
    ResourceNotFoundException,
    SagemakerSQLFault,
    SagemakerSQLError,
    SagemakerSQLApiHandlerError,
)
from amazon_sagemaker_sql_editor.utils.validators import validate_connection_input


class BaseHandler(JupyterHandler):
    def log_request_parameters(self):
        # Request ID is in the URI. For example
        # /api/data-sources?1730847982916
        # /api/connection/Test?1730848226305
        self.log.info(f"Request URI: {self.request.uri}")


class ConnectionsHandler(BaseHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        """Implement this method to handle streamed request data."""
        return

    def handle_endpoint_connection_error(self, error):
        """Handle EndpointConnectionError across handler methods."""
        self.log.error(f"EndpointConnectionError error: {error}")
        traceback.print_tb(error.__traceback__)
        self.set_status("503")
        # TODO: exact error message to be updated after PM sign off.
        self.finish(
            {
                "message": "{}. Please check your network settings or contact support for assistance.".format(
                    str(e)
                ),
            }
        )

    @tornado.web.authenticated
    async def get(self):
        """
        Handles incoming requests to the API: GET./api/connections
        :return:
        """
        try:
            self.log_request_parameters()
            connection_filter_source = self.get_query_argument(
                ConnectionsApiQueryArgs.FILTER_SOURCE, default=None
            )
            connection_filter_type = self.get_query_argument(
                ConnectionsApiQueryArgs.FILTER_TYPE, default=None
            )
            enable_default_athena = self.get_query_argument(
                ConnectionsApiQueryArgs.ENABLE_DEFAULT_ATHENA, default=None
            )

            self.log.debug(
                f"Received request: {Api.PREFIX_GET.value}{Api.NAME_CONNECTIONS.value}.  "
                f"Query param '{ConnectionsApiQueryArgs.FILTER_SOURCE}'={connection_filter_source}"
            )

            response = await GetConnectionsApiService().get_response(
                connection_filter_type=connection_filter_type,
                connection_filter_source=connection_filter_source,
                enable_default_athena=enable_default_athena,
            )
            response = json.dumps(response)

            await self.finish(response)

        except SagemakerSQLFault as error:
            self.log.error(f"Server error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish(
                {
                    "message": "A server error occurred",
                }
            )
        except SagemakerSQLError as error:
            self.log.error(f"Client error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish(
                {
                    "message": str(error),
                }
            )
        except botocore.exceptions.ClientError as error:
            self.log.error(f"Client error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(error.response["ResponseMetadata"]["HTTPStatusCode"])
            await self.finish(
                {
                    "message": error.response["Error"]["Message"],
                }
            )
        except botocore.exceptions.EndpointConnectionError as error:
            await self.handle_endpoint_connection_error(error)
        except TypeError as error:  # thrown by json.dumps() when object is not serializable
            self.log.error(f"Server side error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish({"error": "A server error occurred"})
        except Exception as error:
            self.log.error(f"Server side error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish({"error": "A server error occurred"})

    @tornado.web.authenticated
    async def post(self):
        """
        Handles incoming requests to the API: POST./api/connections
        :return:
        """
        try:
            self.log_request_parameters()
            # retrieve body params
            request_body = self.get_json_body()
            name = request_body.get(ConnectionsApiBodyArgs.NAME)
            description = request_body.get(ConnectionsApiBodyArgs.DESCRIPTION)
            connection_type = request_body.get(ConnectionsApiBodyArgs.CONNECTION_TYPE)
            connection_properties = request_body.get(ConnectionsApiBodyArgs.CONNECTION_PROPERTIES)
            validate_connection_input(
                name=name,
                description=description,
                connection_type=connection_type,
                connection_properties=connection_properties,
            )
            response = await CreateConnectionApiService().create_connection(
                name=name,
                description=description,
                connection_type=connection_type,
                connection_properties=connection_properties,
                current_user=self.get_current_user().name,
            )
            response = json.dumps(response)
            await self.finish(response)
        except AccessDeniedError as error:
            self.log.error(error)
            self.set_status(HTTPStatus.FORBIDDEN.real)
            await self.finish(
                {
                    "error": "You do not have permission to create a connection. Please contact your administrator."
                }
            )
        except InvalidInputException as error:
            self.log.error(error)
            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish({"error": str(error)})
        except DuplicateResourceException as error:
            self.log.error(error)
            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish({"error": "Connection with given name already exists."})
        except HTTPError as error:
            self.log.error(error)
            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish({"error": str(error)})
        except botocore.exceptions.EndpointConnectionError as error:
            await self.handle_endpoint_connection_error(error)
        except Exception as error:
            self.log.error(error)
            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish({"error": error.__traceback__})


class ConnectionEntryHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, connection_name):
        """
        Handles incoming requests to the API: GET./api/connection/<connection_name>
        :return:
        """
        try:
            self.log_request_parameters()
            connection = await GetConnectionApiService().get_connection(
                connection_name=connection_name
            )
            connection_dict = dataclasses.asdict(
                connection, dict_factory=lambda x: {k: v for (k, v) in x if v is not None}
            )
            response = json.dumps(connection_dict)
            await self.finish(response)
        except ResourceNotFoundException as error:
            self.log.error(error)
            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish({"error": "Connection with given name does not exist."})
        except AccessDeniedError as error:
            self.log.error(error)
            self.set_status(HTTPStatus.FORBIDDEN.real)
            await self.finish(
                {
                    "error": "You do not have permission to this connection. Please contact your administrator."
                }
            )
        except botocore.exceptions.EndpointConnectionError as error:
            await self.handle_endpoint_connection_error(error)
        except Exception as error:
            self.log.error(error)
            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish({"error": error.__traceback__})

    @tornado.web.authenticated
    async def put(self, connection_name):
        """
        Handles incoming requests to the API: PUT./api/connection/<connection_name>
        :return:
        """
        try:
            self.log_request_parameters()
            # retrieve body params
            request_body = self.get_json_body()
            name = request_body.get(ConnectionsApiBodyArgs.NAME)
            description = request_body.get(ConnectionsApiBodyArgs.DESCRIPTION)
            connection_type = request_body.get(ConnectionsApiBodyArgs.CONNECTION_TYPE)
            connection_properties = request_body.get(ConnectionsApiBodyArgs.CONNECTION_PROPERTIES)
            validate_connection_input(
                name=name,
                description=description,
                connection_type=connection_type,
                connection_properties=connection_properties,
            )
            if name != connection_name:
                raise InvalidInputException("Cannot update connection name.")

            response = await UpdateConnectionApiService().update_connection(
                old_name=connection_name,
                new_name=name,
                description=description,
                connection_type=connection_type,
                connection_properties=connection_properties,
            )
            response = json.dumps(response)
            await self.finish(response)
        except ResourceNotFoundException as error:
            self.log.error(error)
            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish({"error": "Connection with given name does not exist."})
        except InvalidInputException as error:
            self.log.error(error)
            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish({"error": str(error)})
        except AccessDeniedError as error:
            self.log.error(error)
            self.set_status(HTTPStatus.FORBIDDEN.real)
            await self.finish(
                {
                    "error": "You do not have permission to update this connection. Please contact your administrator."
                }
            )
        except HTTPError as error:
            self.log.error(error)
            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish({"error": str(error)})
        except botocore.exceptions.EndpointConnectionError as error:
            await self.handle_endpoint_connection_error(error)
        except Exception as error:
            self.log.error(error)
            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish({"error": error.__traceback__})

    @tornado.web.authenticated
    async def delete(self, connection_name):
        """
        Handles incoming requests to the API: DELETE./api/connection/<connection_name>
        :return:
        """
        try:
            self.log_request_parameters()
            response = await DeleteConnectionApiService().delete_connection(name=connection_name)
            response = json.dumps(response)
            await self.finish(response)
        except ResourceNotFoundException as error:
            self.log.error(error)
            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish({"error": "Connection with given name does not exist."})
        except AccessDeniedError as error:
            self.log.error(error)
            self.set_status(HTTPStatus.FORBIDDEN.real)
            await self.finish(
                {
                    "error": "You do not have permission to delete this connection. Please contact your administrator."
                }
            )
        except botocore.exceptions.EndpointConnectionError as error:
            await self.handle_endpoint_connection_error(error)
        except Exception as error:
            self.log.error(error)
            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish({"error": error.__traceback__})


class DataSourcesDetailsHandler(BaseHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        """Implement this method to handle streamed request data."""
        return

    @tornado.web.authenticated
    async def post(self):
        """
        Handles incoming requests to the API: POST./api/data-sources
        :return:
        """
        try:
            self.log_request_parameters()
            # retrieve headers
            headers = self.request.headers
            if_modified_since = headers.get(DataSourcesApiHeaders.IF_MODIFIED_SINCE)

            # retrieve body params
            request_body = self.get_json_body()
            path = request_body.get(DataSourcesApiBodyArgs.PATH)
            refresh = request_body.get(DataSourcesApiBodyArgs.REFRESH)
            page_size = request_body.get(DataSourcesApiBodyArgs.PAGE_SIZE)
            next_token = request_body.get(DataSourcesApiBodyArgs.NEXT_TOKEN)
            enable_default_athena = request_body.get(DataSourcesApiBodyArgs.ENABLE_DEFAULT_ATHENA)

            self.log.debug(
                f"Received request: {Api.PREFIX_POST.value}{Api.NAME_DATA_SOURCES.value}. "
                f"Headers: {headers.get_all()}. "
                f"Body {request_body}"
            )

            if path is None:
                raise SagemakerSQLApiHandlerError(
                    f'Invalid request. Missing body argument "{DataSourcesApiBodyArgs.PATH}"'
                )

            # convert to float
            if_modified_since = float(if_modified_since) if if_modified_since else None

            # call service class to fetch response payload
            modified, response = await PostDataSourcesApiService().get_response(
                path=path,
                refresh=refresh,
                modified_since=if_modified_since,
                next_token=next_token,
                page_size=page_size,
                enable_default_athena=enable_default_athena,
            )

            if refresh:
                await (
                    await SearchService.get_instance(
                        await SchemaManagerService.get_instance(
                            PostDataSourcesApiService(), self.log
                        ),
                        GetConnectionsApiService(),
                        self.log,
                    )
                ).refresh_index_for_path(path, enable_default_athena)

            response = json.dumps(response)

            # send response
            if modified:
                self.set_status(HTTPStatus.OK.real)
                await self.finish(response)
            else:
                self.set_status(HTTPStatus.NOT_MODIFIED.real)
                await self.finish()

        except web.HTTPError as error:
            if re.search("^4\d{2}$", str(error.status_code)):
                self.log.error(f"Client error: {error}")
                traceback.print_tb(error.__traceback__)
                self.set_status(HTTPStatus.BAD_REQUEST.real)
                await self.finish(
                    {
                        "message": str(error),
                    }
                )
            else:
                self.log.error(f"Server error: {error}")
                traceback.print_tb(error.__traceback__)
                self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
                await self.finish(
                    {
                        "message": "A server error occurred",
                    }
                )
        except SagemakerSQLFault as error:
            self.log.error(f"Server error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish(
                {
                    "message": "A server error occurred",
                }
            )
        except SagemakerSQLError as error:
            self.log.error(f"Client error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish(
                {
                    "message": str(error),
                }
            )
        except botocore.exceptions.ClientError as error:
            self.log.error(f"Client error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(error.response["ResponseMetadata"]["HTTPStatusCode"])
            await self.finish(
                {
                    "message": error.response["Error"]["Message"],
                }
            )
        except botocore.exceptions.EndpointConnectionError as error:
            await self.handle_endpoint_connection_error(error)
        except TypeError as error:  # thrown by json.dumps() when object is not serializable
            self.log.error(f"Server side error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish({"error": "A server error occurred"})
        except Exception as error:
            self.log.error(f"Server side error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish({"error": "A server error occurred"})


class DataSourcesAutocompleteHandler(BaseHandler):
    """
    Handler class to manage server requests related to autocompletion capability.
    This class is the first entry-point whenever server requests arrive for /api/data-sources-autocomplete
    """

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        """Implement this method to handle streamed request data."""
        return

    @tornado.web.authenticated
    async def post(self):
        """
        Handles incoming requests to the API: POST./api/data-sources-autocomplete
        :return:
        """
        try:
            self.log_request_parameters()
            # retrieve body params
            request_body = self.get_json_body()
            connection_name = request_body.get(DataSourcesAutocompleteApiBodyArgs.CONNECTION_NAME)

            self.log.debug(
                f"Received request: {Api.PREFIX_POST.value}{Api.NAME_DATA_SOURCES_AUTOCOMPLETE.value}. "
                f"Body {request_body}"
            )

            if connection_name is None:
                raise SagemakerSQLApiHandlerError(
                    f'Invalid request. Missing body argument "{DataSourcesAutocompleteApiBodyArgs.CONNECTION_NAME}"'
                )

            # create server response
            api_service = await PostDataSourcesAutocompleteApiService.get_instance(log=self.log)
            response_status = await api_service.get_response(connection_name=connection_name)

            # send server response
            self.set_status(response_status)
            await self.finish()
        except SagemakerSQLFault as error:
            self.log.error(f"Server error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish(
                {
                    "message": "A server error occurred",
                }
            )
        except SagemakerSQLError as error:
            self.log.error(f"Client error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.BAD_REQUEST.real)
            await self.finish(
                {
                    "message": str(error),
                }
            )
        except botocore.exceptions.EndpointConnectionError as error:
            await self.handle_endpoint_connection_error(error)
        except botocore.exceptions.ClientError as error:
            self.log.error(f"Client error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(error.response["ResponseMetadata"]["HTTPStatusCode"])
            await self.finish(
                {
                    "message": error.response["Error"]["Message"],
                }
            )
        except TypeError as error:  # thrown by json.dumps() when object is not serializable
            self.log.error(f"Server side error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish({"error": "A server error occurred"})
        except Exception as error:
            self.log.error(f"Server side error: {error}")
            traceback.print_tb(error.__traceback__)

            self.set_status(HTTPStatus.INTERNAL_SERVER_ERROR.real)
            await self.finish({"error": "A server error occurred"})


class SearchHandler(BaseHandler):
    """Handler class for search APIs: /api/search. The following methods are supported:

    - GET./api/search: Search for a term across all data sources. Also creates an in-memory
     index the first time a search is requested.
    """

    schema_service: SchemaManagerService = None
    search_service: SearchService = None

    async def _setup(self):
        """Setup SearchService with required services."""

        if not SearchHandler.schema_service:
            self.log.info("Setting up schema_service and search_service")
            SearchHandler.schema_service = await SchemaManagerService.get_instance(
                PostDataSourcesApiService(), log=self.log
            )
            SearchHandler.search_service = await SearchService.get_instance(
                SearchHandler.schema_service, GetConnectionsApiService(), self.log
            )

    async def get(self):
        """Get method handler for /api/smsql/search API.

        Supported request parameters:
        - term: the search query term
        - filters: list containing NodeType(DATABASE/TABLE/SCHEMA) to search amongst
        - highlight: whether to add highlightedName and highlightedPath in the response
        - pageSize: optional value for pagination. Default value is 100, use -1 to return all
        - nextToken: optional value for pagination

        :return: SearchResponse with list of hits, current index status and next_token if any.
        """

        self.log_request_parameters()
        await self._setup()

        term = self.get_query_argument("term", default=None)
        filters = self.get_query_arguments("filters")
        highlight = self.get_query_argument("highlight", default=None)
        page_size = int(self.get_query_argument("pageSize", default="100"))
        next_token = self.get_query_argument("nextToken", default=None)
        enable_default_athena = self.get_query_argument("enableDefaultAthena", default=None)

        request = SearchRequest(
            term, filters, highlight, page_size, next_token, enable_default_athena
        )
        try:
            request.validate_and_sanitize()
        except ValueError as e:
            self.log.error("Error while validating request %s request, error: %s", request, e)
            self.set_status(HTTPStatus.BAD_REQUEST.value)
            await self.finish(
                {
                    "message": str(e),
                }
            )
            return

        results = await SearchHandler.search_service.search(request)
        status = HTTPStatus.OK if SearchHandler.search_service.index_ready else HTTPStatus.ACCEPTED
        self.set_status(status.value)
        await self.finish(results.get_as_json())
