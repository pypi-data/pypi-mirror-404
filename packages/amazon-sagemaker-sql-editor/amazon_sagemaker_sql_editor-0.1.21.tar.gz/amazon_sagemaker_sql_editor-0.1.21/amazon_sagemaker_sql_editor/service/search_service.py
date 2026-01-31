import re
import sqlite3
from sqlite3 import Cursor, Connection
from typing import List, Dict, Optional, Union

from tornado.locks import Lock

from amazon_sagemaker_sql_execution.utils.metrics.service_metrics import (
    ClassAttributeMetricsContextMixin,
)
from amazon_sagemaker_sql_editor.model.models import (
    IndexStatus,
    SearchRequest,
    SearchResponse,
)
from amazon_sagemaker_sql_editor.service.api_service import GetConnectionsApiService
from amazon_sagemaker_sql_editor.service.schema_service import (
    GetSchemaResponse,
    GetSchemaRequest,
    SchemaManagerService,
)
from amazon_sagemaker_sql_editor.utils.constants import PathEnum, NodeType
from amazon_sagemaker_sql_editor.utils.exceptions import SagemakerSQLFault
from amazon_sagemaker_sql_editor.utils.metrics.service_metrics import (
    async_add_metrics,
)


class SearchService(ClassAttributeMetricsContextMixin):
    INDEX_TABLE_NAME = "search_index"
    CONNECTION_NAME = "file:smsql_search?mode=memory&cache=shared"
    # define the NodeType which will be indexed
    NODE_TYPES_TO_INDEX = [
        node_type.value
        for node_type in [
            NodeType.DATA_SOURCE,
            NodeType.DATABASE,
            NodeType.SCHEMA,
            NodeType.TABLE,
        ]
    ]
    _instance = None
    instance_lock = Lock()
    _index_status = dict()
    _index = sqlite3.connect(CONNECTION_NAME, uri=True)
    index_ready = False
    _lock = Lock()
    log = None
    schema_service = None
    get_connections_api_service = None

    def __new__(
        cls,
        schema_service: SchemaManagerService,
        get_connections_api_service: GetConnectionsApiService,
        log,
        *args,
        **kwargs,
    ):
        # if instance is None, create and store new instance
        if not cls._instance:
            instance = super().__new__(cls, *args, **kwargs)
            instance.log = log
            instance.schema_service = schema_service
            instance.get_connections_api_service = get_connections_api_service
            instance._create_index_table(SearchService.INDEX_TABLE_NAME)
            instance.schema_service.register_success_callback(instance.index_callback)
            instance.schema_service.register_failure_callback(instance.handle_error_callback)
            cls._instance = instance
        # return the stored instance
        return cls._instance

    @classmethod
    async def get_instance(
        cls,
        schema_service: SchemaManagerService,
        get_connections_api_service: GetConnectionsApiService,
        log,
    ):
        async with cls.instance_lock:
            return cls.__new__(
                cls,
                schema_service=schema_service,
                get_connections_api_service=get_connections_api_service,
                log=log,
            )

    def _create_index_table(self, index_table_name: str):
        self._index.execute(
            f"""
            CREATE TABLE {index_table_name}(
                name TEXT, path COLLATE NOCASE, type TEXT, sampleQuery TEXT
            );
            """
        )

    async def _remove_from_index_with_connection(self, path_prefix, conn):
        conn.execute(
            f"DELETE FROM {SearchService.INDEX_TABLE_NAME} WHERE path LIKE '{path_prefix}%'"
        )
        conn.commit()

    async def _initialize_index(self, enable_default_athena) -> bool:
        """Initialize the search index with the all the connections' data by calling GetConnectionsApiService.

        :return: Return updated index status, True if initialize complete otherwise False
        """
        # call get_connections
        connections_response = (
            await GetConnectionsApiService().get_response(
                enable_default_athena=enable_default_athena
            )
        )["connections"]
        connections = [connection_detail["name"] for connection_detail in connections_response]
        un_indexed_connections = await self.get_unindexed_connections(connections)
        if len(un_indexed_connections) == 0:
            self.index_ready = True
            return True
        else:
            for connection_name in un_indexed_connections:
                await self.set_index_status(connection_name, IndexStatus.Status.IN_PROGRESS)
                await self.schema_service.submit_request(
                    GetSchemaRequest(
                        path=connection_name,
                        refresh=False,
                        enable_default_athena=enable_default_athena,
                    )
                )
                self.log.info("Request added to index %s", connection_name)
            return False

    @async_add_metrics("SearchApi")
    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Search for any connection, schema, database or table across indexed connections.
        :param request: SearchRequest containing term, filters and pagintion params
        :return: SearchResponse containing hits and current index status
        """

        if not self.index_ready:
            updated_index_ready = await self._initialize_index(request.enable_default_athena)
            if not updated_index_ready:
                self.metrics_context.set_property("IndexReady", 0)
                return SearchResponse(
                    hits=list(),
                    indexes=self.get_index_status(),
                    nextToken=None,
                )
        self.metrics_context.set_property("IndexReady", 1)

        limit_clause = ""
        offset_clause = ""
        if request.page_size != -1:
            limit_clause = f"LIMIT {request.page_size}"
        if request.next_token:
            offset_clause = f"OFFSET {request.offset}"
        query = f"""
            SELECT
                name, type, path, sampleQuery
            FROM
                {SearchService.INDEX_TABLE_NAME}
            WHERE path LIKE ?
                {self._build_where_clause_for_filter(request)}
            ORDER BY
                path, name
            {limit_clause}
            {offset_clause}
        """
        search_term = f"%{request.term}%"
        response = (await self._execute_with_params(query, (search_term,))).fetchall()

        hits = []
        if request.highlight:
            regex = re.compile(re.escape(request.term), re.IGNORECASE)
        for hit_tuple in response:
            hit = SearchResponse.Hit(
                name=hit_tuple[0],
                nodeType=hit_tuple[1],
                data=SearchResponse.Hit.Data(
                    path=hit_tuple[2],
                    highlightedName=None,
                    highlightedPath=None,
                    sampleQuery=hit_tuple[3],
                    connectionName=hit_tuple[2].split("/")[0].strip(),
                ),
            )
            if request.highlight:
                assert regex
                hit.data.highlightedName = regex.sub(
                    lambda match: f"<mark>{match.group()}</mark>", hit_tuple[0]
                )
                hit.data.highlightedPath = regex.sub(
                    lambda match: f"<mark>{match.group()}</mark>", hit_tuple[2]
                )
            hits.append(hit)

        indexes = self.get_index_status()
        self.metrics_context.set_property("NumberOfHits", len(hits))
        self.metrics_context.set_property(
            "NumberOfSuccessfulIndexes",
            len(
                list(filter(lambda index: index.indexStatus == IndexStatus.Status.SUCCESS, indexes))
            ),
        )
        self.metrics_context.set_property(
            "NumberOfFailedIndexes",
            len(
                list(filter(lambda index: index.indexStatus == IndexStatus.Status.FAILED, indexes))
            ),
        )
        return SearchResponse(
            hits=hits,
            indexes=indexes,
            nextToken=self.generate_next_token(request, len(response)),
        )

    async def refresh_index_for_path(self, path: str, enable_default_athena: bool):
        # when refreshing a specific node of a connection
        if PathEnum.DELIMITER in path:
            raise NotImplementedError("Refreshing partial connection is not supported.")
        if path == "":
            # when refreshing all connections
            connections_response = (
                await self.get_connections_api_service.get_response(
                    enable_default_athena=enable_default_athena
                )
            )["connections"]
            connections = [connection_detail["name"] for connection_detail in connections_response]
        else:
            # when refreshing a single connection
            connections = [path]

        for connection_name in connections:
            await self.set_index_status(connection_name, IndexStatus.Status.IN_PROGRESS)
            await self.schema_service.submit_request(
                GetSchemaRequest(
                    path=connection_name, refresh=True, enable_default_athena=enable_default_athena
                )
            )
            self.log.info("Request added to index %s", connection_name)

    async def get_unindexed_connections(
        self, connection_names: Optional[List[str]] = None
    ) -> List[str]:
        """
        Compares the given list with the internal index status and returns any connections which are not yet indexed.
        i.e. does not have SUCCESS or FAILED status.
        :param connection_names:
        :return:
        """

        async with self._lock:
            if not connection_names:
                return [
                    name
                    for name, status in self._index_status.items()
                    if status.indexStatus == IndexStatus.Status.IN_PROGRESS
                ]
            return list(
                set(connection_names)
                - set(
                    [
                        name
                        for name, status in self._index_status.items()
                        if status.indexStatus
                        in [IndexStatus.Status.SUCCESS, IndexStatus.Status.FAILED]
                    ]
                )
            )

    async def set_index_status(self, connection_name: str, status: IndexStatus.Status):
        async with self._lock:
            self._index_status[connection_name] = IndexStatus(
                connectionName=connection_name, indexStatus=status
            )

    async def index_callback(self, response: GetSchemaResponse):
        """Function to call after successfully fetching the schema via SchemaService.

        Creates a new sql connection to the database and indexes all items in a single transaction
        """

        root_item = response.get_root_item_name()
        try:
            with sqlite3.connect(SearchService.CONNECTION_NAME, uri=True) as conn:
                await self._remove_from_index_with_connection(response.get_root_item_name(), conn)
                await self._index_node(response.nodeList, PathEnum.ROOT, conn)
                conn.commit()
        except sqlite3.Error as e:
            self.log.error("Error while indexing %s, error: %s", root_item, e)
            if self._index_status.get(root_item, None) in [None, IndexStatus.Status.FAILED]:
                await self.set_index_status(root_item, IndexStatus.Status.FAILED)
            else:
                # TODO: replace SUCCESS with REFRESH_FAILED once we have UX for it
                await self.set_index_status(root_item, IndexStatus.Status.SUCCESS)
        else:
            await self.set_index_status(root_item, IndexStatus.Status.SUCCESS)
        finally:
            self.log.info("Indexing complete for %s", root_item)

    async def handle_error_callback(self, request: GetSchemaRequest, exception: Exception):
        """Function to call after failure while fetching the schema via SchemaService."""

        self.log.error(
            "Could not index %s because of error %s",
            request.path,
            exception,
        )
        async with self._lock:
            self.log.info("adding to indexed set %s", request.path)
            self._index_status[request.path] = IndexStatus(
                connectionName=request.path, indexStatus=IndexStatus.Status.FAILED
            )
            self.log.info("now indexed %s", self._index_status)

        raise exception

    def _build_where_clause_for_filter(self, request: SearchRequest):
        """Generate sql WHERE clause for a search query based on request.

        - If request contains filters then add a WHERE clause filtering only the requested type
        """

        if len(request.filters) != 0:
            type_clause = ",".join([f"'{x}'" for x in request.filters])
            type_clause = f" AND type IN ({type_clause})"
            return type_clause

        return ""

    def get_index_status(self) -> List[IndexStatus]:
        return list(self._index_status.values())

    def generate_next_token(self, request: SearchRequest, response_size: int) -> Union[str, None]:
        """Generates a next_token for the response based on the request."""

        if request.page_size == -1 or response_size < request.page_size:
            return None
        return SearchRequest.encode_next_token(
            request.page_size, request.offset + request.page_size
        )

    def _build_node_path(self, name: str, path: str):
        if path == PathEnum.ROOT:
            return name
        else:
            return f"{path}{PathEnum.DELIMITER}{name}"

    async def _index_node(
        self, node: Dict[str, GetSchemaResponse.Item], path: str, conn: Connection
    ):
        try:
            if not node:
                return
            for key, value in node.items():
                # only index allow-listed nodeTypes
                if value.nodeType not in SearchService.NODE_TYPES_TO_INDEX:
                    continue
                full_path = self._build_node_path(key, path)
                conn.execute(
                    f"INSERT INTO {SearchService.INDEX_TABLE_NAME} VALUES(?, ?, ?, ?);",
                    (key, full_path, value.nodeType, value.nodeData.sampleQuery),
                )
                if value.nodeList:
                    await self._index_node(value.nodeList, full_path, conn)
        except Exception:
            raise SagemakerSQLFault(f"error while indexing node: {node}")

    async def _execute(self, query: str) -> Cursor:
        return self._index.execute(query)

    async def _execute_with_params(self, query: str, params: tuple) -> Cursor:
        return self._index.execute(query, params)
