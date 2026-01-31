import asyncio
from datetime import timedelta
from typing import Union, Dict, Callable, Awaitable, Optional

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.locks import Lock, Semaphore

from amazon_sagemaker_sql_execution.utils.metrics.service_metrics import (
    InstanceAttributeMetricsContextMixin,
)

from amazon_sagemaker_sql_editor.service.api_service import PostDataSourcesApiService
from amazon_sagemaker_sql_editor.utils.constants import (
    DataSourcesApiResponse,
    PathEnum,
    NodeType,
)
from amazon_sagemaker_sql_editor.model.models import (
    GetSchemaRequest,
    GetSchemaResponse,
    NodeData,
)
from amazon_sagemaker_sql_editor.utils.metrics.service_metrics import (
    async_add_metrics,
)


class SchemaManagerService:
    """
    Class to facilitate crawling data sources and generate schema.

    It also de-dupes requests for the same data source and makes sure that no more than a predefined number of
    data sources are being crawled at a time.
    """

    active_workers: Dict[int, "GetSchemaWorker"] = dict()
    _lock = Lock()
    _instance = None
    instance_lock = Lock()
    data_sources_api_service = None
    log = None
    _success_callbacks = []
    _failure_callbacks = []

    def __new__(cls, data_sources_api_service: PostDataSourcesApiService, log, *args, **kwargs):
        if not cls._instance:
            instance = super().__new__(cls, *args, **kwargs)
            instance.data_sources_api_service = data_sources_api_service
            instance.log = log
            cls._instance = instance
        return cls._instance

    @classmethod
    async def get_instance(cls, data_sources_api_service: PostDataSourcesApiService, log):
        async with cls.instance_lock:
            return cls.__new__(cls, data_sources_api_service=data_sources_api_service, log=log)

    async def submit_request(self, request: GetSchemaRequest) -> None:
        """
        Submit a request to crawl a data source. The process will initiate if there are <5 requests being processed.
        :param request: GetSchemaRequest to add to the request queue
        """

        async with SchemaManagerService._lock:
            if request.__hash__() in SchemaManagerService.active_workers:
                self.log.info("Request already in progress %s", request.path)
                return
            worker = GetSchemaWorker(
                request,
                data_sources_api_service=self.data_sources_api_service,
                log=self.log,
            )
            worker.set_on_complete_callback(self._on_work_complete)
            SchemaManagerService.active_workers[request.__hash__()] = worker
            IOLoop.current().add_callback(worker.execute)

    def register_success_callback(self, callback: Callable[[GetSchemaResponse], Awaitable[None]]):
        """
        Register a callback function which will be executed when crawling successfully completed.
        :param callback:
        :return:
        """

        self._success_callbacks.append(callback)

    def register_failure_callback(
        self, callback: Callable[[GetSchemaRequest, Exception], Awaitable[None]]
    ):
        """
        Register a callback function which will be executed when crawling is completed with a failure.
        :param callback:
        :return:
        """

        self._failure_callbacks.append(callback)

    async def _on_work_complete(
        self,
        request: GetSchemaRequest,
        response: Optional[GetSchemaResponse],
        exception: Optional[Exception],
    ):
        """
        This is executed when crawling is complete, it is used to perform operation post crawling like
        executing registered callbacks and some other housekeeping operations.
        :param request: The completed GetSchemaRequest
        :param response: GetSchemaResponse if successful without any exceptions
        :param exception: Exception if unsuccessful due to any exception
        """

        async with SchemaManagerService._lock:
            if request.__hash__() in SchemaManagerService.active_workers:
                self.log.info("Work complete for %s, removing from active_workers", request.path)
                del SchemaManagerService.active_workers[request.__hash__()]

        # TODO: make all callbacks parallel
        if response:
            for callback in self._success_callbacks:
                await callback(response)
        if exception:
            for callback in self._failure_callbacks:
                try:
                    await callback(request, exception)
                except Exception:
                    self.log.warning(
                        "Silently logging error from callback %s",
                        request.path,
                        exc_info=True,
                    )

        request.finish_request()
        self.log.info(
            "Crawled %s and executed callbacks in %.2f ms",
            request.path,
            request.time_elapsed,
        )


class GetSchemaWorker(InstanceAttributeMetricsContextMixin):
    _semaphore = Semaphore(3)
    # define what NodeType would be crawled
    # SCHEMA is required as snowflake stores tables as children of schema
    NODE_TYPES_TO_CRAWL = [
        node_type.value
        for node_type in [
            NodeType.ROOT,
            NodeType.DATA_SOURCE,
            NodeType.DATABASE,
            NodeType.SCHEMA,
        ]
    ]

    def __init__(
        self,
        request: GetSchemaRequest,
        data_sources_api_service,
        batch_size: int = 3,
        log=None,
    ):
        super().__init__()
        self.data_sources_api_service = data_sources_api_service
        self.request = request
        self.batch_size = batch_size
        self.response: Union[GetSchemaResponse, None] = None
        self._on_complete_callback: Union[
            Callable[
                [GetSchemaRequest, Optional[GetSchemaResponse], Optional[Exception]],
                Awaitable[None],
            ],
            None,
        ] = None
        self.log = log

    @async_add_metrics("GetSchema")
    async def execute(self) -> None:
        """
        The primary function which starts the execution of the worker.
        :return:
        """

        async with self._semaphore:
            path = self.request.path
            self.log.info("Starting worker for %s", path)
            try:
                await self._get_data_for_all_levels(path, parent_response_item=None)
            except Exception as e:
                await self._on_complete_callback(self.request, None, e)
            else:
                await self._on_complete_callback(self.request, self.response, None)

        self.metrics_context.set_property("TimeElapsed", self.request.time_elapsed)
        self.metrics_context.set_property("Path", self.request.path)
        self.metrics_context.set_property("Refresh", self.request.refresh)

    def set_on_complete_callback(
        self,
        callback: Callable[
            [GetSchemaRequest, Optional[GetSchemaResponse], Optional[Exception]],
            Awaitable[None],
        ],
    ):
        self._on_complete_callback = callback

    def _build_root_to_response(self, request_path, response):
        schema_root = GetSchemaResponse(
            {
                request_path: GetSchemaResponse.Item(
                    name=request_path,
                    nodeType=response["nodeType"],
                    lastUpdateTime=response[DataSourcesApiResponse.LAST_UPDATE_TIME_KEY],
                    nodeData=NodeData(source="", type=response["nodeType"]),
                    nodeList=dict(),
                )
            }
        )
        return schema_root

    async def _get_data_for_all_levels(
        self, path: str, parent_response_item: GetSchemaResponse.Item = None
    ) -> None:
        """
        Method to create the entire information schema under a particular path as tree representation.
        - Makes recursive calls to 'class PostDataSourcesApiService -> get_response()' method for fetching data
         node-level by node-level.
        - Implements a batching system to parallelize API calls at a node-level (upto a threshold)

        :param path:
        :param parent_response_item:
        :return:
        """

        # page_size = -1 to skip paginating the responses
        _, response = await gen.with_timeout(
            timedelta(seconds=30),
            self.data_sources_api_service.get_response(
                path=path,
                refresh=self.request.refresh,
                page_size=-1,
                enable_default_athena=self.request.enable_default_athena,
            ),
        )

        if not parent_response_item:
            self.response = self._build_root_to_response(path, response)
            parent_response_item = self.response.nodeList.get(path)

        response_node_list = response[DataSourcesApiResponse.NODE_LIST_KEY]

        batch_requests = []
        for i, node in enumerate(response_node_list or []):
            node_data = node[DataSourcesApiResponse.NODE_DATA_KEY]
            child_response_item = GetSchemaResponse.Item(
                name=node[DataSourcesApiResponse.NAME_KEY],
                nodeType=node["nodeType"],
                lastUpdateTime=node[DataSourcesApiResponse.LAST_UPDATE_TIME_KEY],
                nodeData=NodeData(
                    sampleQuery=node_data.get("sampleQuery", None),
                    source=node_data.get("source", None),
                    type=node_data.get("type", None),
                ),
                nodeList=dict(),
            )
            parent_response_item.nodeList[node[DataSourcesApiResponse.NAME_KEY]] = (
                child_response_item
            )

            if (not node[DataSourcesApiResponse.IS_LEAF_KEY]) and node[
                "nodeType"
            ] in GetSchemaWorker.NODE_TYPES_TO_CRAWL:
                node_path = f"{path}{PathEnum.DELIMITER}{node[DataSourcesApiResponse.NAME_KEY]}"

                # append tasks to list to create a batch
                batch_requests.append(
                    asyncio.get_running_loop().create_task(
                        self._get_data_for_all_levels(
                            node_path,
                            parent_response_item.nodeList[node[DataSourcesApiResponse.NAME_KEY]],
                        )
                    )
                )

            if (i + 1) % self.batch_size == 0 or (i + 1) == len(response_node_list):
                # either the batch size limit or the node children limit reached, 'await' till the batch completes
                # processing. this is done to avoid throttling issues from the underlying data-source's end as well
                # as to avoid overloading server capacity.
                await asyncio.gather(*batch_requests)
                # accumulate responses from all batches
                # reset batch list
                batch_requests = []
