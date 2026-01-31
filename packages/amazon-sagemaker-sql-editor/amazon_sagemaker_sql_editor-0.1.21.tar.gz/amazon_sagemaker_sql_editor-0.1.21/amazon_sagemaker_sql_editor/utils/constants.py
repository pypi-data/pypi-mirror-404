# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from enum import Enum, EnumMeta

from sagemaker_jupyterlab_extension_common.dual_stack_utils import is_dual_stack_enabled

SERVER_EXTENSION_APP_NAME = "amazon_sagemaker_sql_editor"
USE_DUALSTACK_ENDPOINT = is_dual_stack_enabled()


class MetaEnum(EnumMeta):
    """
    Helper class for Enum classes to enable checks using 'in' operator
    """

    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class ConnectionsApiQueryArgs:
    """
    Request query parameters for GET./api/connections
    """

    FILTER_SOURCE = "filterSource"  # to filter based on connection source
    FILTER_TYPE = "filterType"  # to filter based on connection type
    ENABLE_DEFAULT_ATHENA = "enableDefaultAthena"


class DataSourcesApiBodyArgs:
    """
    Request body parameters for POST./api/data-sources
    """

    PATH = "path"
    REFRESH = "refresh"
    PAGE_SIZE = "pageSize"
    NEXT_TOKEN = "nextToken"
    ENABLE_DEFAULT_ATHENA = "enableDefaultAthena"


class DataSourcesAutocompleteApiBodyArgs:
    """
    Request body parameters for POST./api/data-sources-autocomplete
    """

    CONNECTION_NAME = "connectionName"


class DataSourcesApiHeaders:
    IF_MODIFIED_SINCE = "If-Modified-Since"


class DataSourcesApiResponse:
    LAST_UPDATE_TIME_KEY = "lastUpdateTime"
    NODE_LIST_KEY = "nodeList"
    NODE_DATA_KEY = "nodeData"
    IS_LEAF_KEY = "isLeaf"
    NAME_KEY = "name"
    TYPE_KEY = "type"
    NEXT_TOKEN_KEY = "nextToken"


class DataSourcesConstants:
    CONNECTION_TYPE_GLUE = "GLUE_CONNECTION"


class PathEnum:
    ROOT = ""
    DELIMITER = "/"


class CacheLocation:
    LOCAL_PARENT_DIR = "~/sagemaker-sql-editor"
    SAGEMAKER_PARENT_DIR = "/home/sagemaker-user"
    API_SUB_DIR = ".sagemaker_sql_editor_api_cache"


class ClientType(Enum):
    BOTO = "boto"
    SQL = "sql_execution"


class DataSourceType(Enum, metaclass=MetaEnum):
    GLUE = "GLUE"
    REDSHIFT = "REDSHIFT"
    ATHENA = "ATHENA"
    SNOWFLAKE = "SNOWFLAKE"


class AutocompleteApiConstants:
    SCHEMA_DIR = "/opt/amazon/sagemaker/user-data/autocomplete-schema"
    CENTRAL_SCHEMA_FILENAME = "sql-language-server-schema.json"

    CONNECTION_STATUS_IN_PROGRESS = "in_progress"
    CONNECTION_STATUS_CLIENT_ERROR = "client-error"
    CONNECTION_STATUS_SERVER_ERROR = "server-error"

    RESPONSE_NOT_MODIFIED = "not-modified"


API_NAMESPACE = "/api"


class Api(Enum):
    PREFIX_GET = "GET."
    PREFIX_POST = "POST."
    NAME_CONNECTION = f"{API_NAMESPACE}/connection"
    NAME_CONNECTIONS = f"{API_NAMESPACE}/connections"
    NAME_DATA_SOURCES = f"{API_NAMESPACE}/data-sources"
    NAME_DATA_SOURCES_AUTOCOMPLETE = f"{API_NAMESPACE}/data-sources-autocomplete"
    NAME_SEARCH = f"{API_NAMESPACE}/smsql/search"


class NodeType(Enum):
    ROOT = "ROOT"
    DATA_SOURCE = "DATA_SOURCE"
    DATABASE = "DATABASE"
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    SCHEMA = "SCHEMA"


class LoggerDetails:
    SAGEMAKER_SQL_EDITOR_LOG_FILE = "notebook_sql_editor.log"
    LOGGER_NAME = "sagemaker-notebook-sql-editor"


class MetricsConstants:
    HTTP_SUCCESS_CODE = "200"
    HTTP_SERVER_ERROR_CODE = "500"


class DefaultAthena:
    CONNECTION_NAME = "default-athena-connection"
    CONNECTION_TYPE = "ATHENA"
    CONNECTION_DESCRIPTION = "Connection that uses default credentials to connect to Athena"
    LAST_UPDATED_TIME = 1


class ConnectionsApiBodyArgs:
    """
    Request body parameters for POST./api/connections
    """

    NAME = "name"  # name of the connection
    DESCRIPTION = "description"  # description for the connection
    CONNECTION_TYPE = "connectionType"  # type of the connection
    CONNECTION_PROPERTIES = "connectionProperties"  # Connection properties


class GlueConnectionType(Enum, metaclass=MetaEnum):
    REDSHIFT = "REDSHIFT"
    ATHENA = "ATHENA"
    SNOWFLAKE = "SNOWFLAKE"
