# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import base64
import dataclasses
import json
import time
from enum import Enum
from typing import List, Union, Dict, Optional, Tuple
from dataclasses import dataclass

from amazon_sagemaker_sql_editor.utils.constants import NodeType


@dataclass
class ConnectionMetadataModel:
    description: str


@dataclass
class ConnectionModel:
    name: str
    type: str
    source: str
    metadata: ConnectionMetadataModel
    lastUpdateTime: float


@dataclass
class ConnectionsResponseModel:
    connections: List[ConnectionModel]


@dataclass
class DataSourcesNodeDataModel:
    source: str
    type: str
    sampleQuery: str = None


@dataclass
class DataSourcesTableNodeDataModel(DataSourcesNodeDataModel):
    """
    Model class to hold `nodeData` properties for node of type TABLE
    """

    tableMetadata: Dict[str, str] = None


@dataclass
class DataSourcesColumnNodeDataModel(DataSourcesNodeDataModel):
    """
    Model class to hold `nodeData` properties for node of type COLUMN
    """

    columnType: str = None


@dataclass
class DataSourcesNodeResponseModel:
    isLeaf: bool
    lastUpdateTime: float
    name: str = None
    nodeType: str = None
    nodeData: DataSourcesNodeDataModel = None
    nodeList: List["DataSourcesNodeResponseModel"] = None


@dataclass
class GetSchemaRequest:
    """
    Model class which contains details for a request to fetch schema for a given connection_name.
    """

    def __init__(self, path: str, refresh: bool, enable_default_athena: bool):
        # request properties
        self.path = path
        self.refresh = refresh
        self.enable_default_athena = enable_default_athena

        # context properties
        self._start_time = time.monotonic_ns()
        self.time_elapsed = None

    def __hash__(self):
        return hash((self.path, self.refresh))

    def finish_request(self):
        """Perform operations at the end of a request. Currently, includes saving
        time_elapsed for request.
        """

        self.time_elapsed = (time.monotonic_ns() - self._start_time) / 1000000


NodeData = DataSourcesNodeDataModel


@dataclass
class GetSchemaResponse:
    """
    Model class which contains response for a `GetSchemaRequest` request.
    """

    nodeList: Union[Dict[str, "Item"], None] = None

    def get_root_item_name(self):
        """
        Get the name of root node Item in GetSchemaResponse.
        :return:
        """

        if not self.nodeList:
            return None
        return next(iter(self.nodeList.keys()))

    @dataclass
    class Item:
        """
        Model class which contains details of a single item in GetSchemaResponse.

        It contains:
        - name: name of the item/node
        - nodeType: type of the node e.g. DATABASE, SCHEMA, TABLE etc.
        - lastUpdateTime: the lastUpdateTime if fetched from cache
        - nodeData: key-value pair containing optional node date
        - nodeList: a list of all children of the node
        """

        name: str
        nodeType: str
        lastUpdateTime: int
        nodeData: Union[NodeData, None]
        nodeList: Union[Dict[str, "GetSchemaResponse.Item"], None]

        def __str__(self):
            return json.dumps(
                {
                    "name": self.name,
                    "nodeType": self.nodeType,
                    "lastUpdateTime": self.lastUpdateTime,
                    "nodeData": self.nodeData,
                    "nodeList": list(self.nodeList.keys()),
                }
            )


@dataclass
class SearchRequest:
    """
    A request to search across all data sources using the /api/search API.

    - term: the search query term
    - filters: list containing NodeType(DATABASE/TABLE/SCHEMA) to search amongst
    - highlight: whether to add highlightedName and highlightedPath in the response
    - page_size: used for pagination, set as 100 if not provided. Can be set to -1 to return all
    - next_token: optional value for pagination
    """

    term: str
    filters: List[str]
    highlight: Optional[bool]
    page_size: Optional[int]
    next_token: Optional[str]
    offset = 0
    enable_default_athena: Optional[bool]

    @classmethod
    def decode_next_token(cls, next_token: str) -> Tuple[Union[int, None], Union[int, None]]:
        """Decode a string to a tuple containing page_size and offset."""

        try:
            json_string = base64.urlsafe_b64decode(next_token.encode()).decode()
            next_token_dict = json.loads(json_string)
            return next_token_dict.get("pageSize", None), next_token_dict.get("offset", None)
        except Exception as e:
            raise ValueError(f"Exception while decoding nextToken {next_token}") from e

    @classmethod
    def encode_next_token(cls, page_size: int, offset: int) -> str:
        """Encode page_size and offset to a token string based on base64 encoding."""

        token_content = json.dumps({"offset": offset, "pageSize": page_size})
        return base64.urlsafe_b64encode(token_content.encode()).decode()

    def validate_and_sanitize(self):
        """Validate a SearchRequest and raise ValueError if invalid request."""

        if not self.term or len(self.term) < 3:
            raise ValueError("term must be present and of length greater than 2")
        if self.page_size > 10000:
            raise ValueError("pageSize cannot be more than 10000")
        if self.page_size != -1 and self.page_size < 1:
            raise ValueError("pageSize must either be -1 or a positive integer")
        if self.next_token and self.page_size == -1:
            raise ValueError("nextToken cannot cannot be used with pageSize -1")
        try:
            filters = [NodeType[x].value.__str__() for x in self.filters if x.strip()]
            self.filters = filters
        except KeyError as e:
            raise ValueError(f"{e} is not a valid filter for search")

        if self.next_token:
            # override page_size if next_token in present
            self.page_size, self.offset = SearchRequest.decode_next_token(self.next_token)


@dataclass
class SearchResponse:
    """
    Response for the /api/search API.
    """

    hits: List["Hit"]
    nextToken: Union[str, None]
    indexes: List["IndexStatus"]

    @dataclass
    class Hit:
        """
        One single search hit in a SearchResponse.
        """

        nodeType: str
        name: str
        data: "Data"

        @dataclass
        class Data:
            """
            Data for a Hit in SearchResponse.
            """

            path: str
            highlightedName: Union[str, None]
            highlightedPath: Union[str, None]
            sampleQuery: Union[str, None]
            connectionName: str

    def get_as_json(self):
        """
        Get json representation of the response.
        :return:
        """

        return dataclasses.asdict(
            self, dict_factory=lambda x: {k: transform_enum(v) for (k, v) in x if v is not None}
        )


@dataclass
class IndexStatus:
    """
    Class indicating current status of the indexes which are used to facilitate search.
    """

    connectionName: str
    indexStatus: "Status"

    class Status(Enum):
        """
        Enum stating the current status of a connection's index.
        """

        IN_PROGRESS = "IN_PROGRESS"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"


def transform_enum(a):
    """
    Transform any Enum to its name, leaves all other types as is.
    :param a:
    :return:
    """

    if isinstance(a, Enum):
        return a.name
    return a


@dataclass
class GlueConnectionModel:
    name: str
    description: str
    connectionType: str
    connectionProperties: str
    lastUpdateTime: float
