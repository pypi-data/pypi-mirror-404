# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

from amazon_sagemaker_sql_editor.adapter.adapters import PostDataSourcesResponseAdapter
from amazon_sagemaker_sql_editor.model.models import (
    NodeType,
    DataSourcesNodeResponseModel as NodeResponseModel,
    DataSourcesNodeDataModel as NodeDataModel,
    DataSourcesTableNodeDataModel as TableNodeDataModel,
    DataSourcesColumnNodeDataModel as ColumnNodeDataModel,
)
from amazon_sagemaker_sql_editor.utils.constants import (
    DataSourceType,
    DataSourcesConstants,
)
from amazon_sagemaker_sql_editor.utils.date_time import (
    current_time_utc,
    convert_datetime_format,
)

from amazon_sagemaker_sql_editor.utils.exceptions import (
    SagemakerSQLResponseAdapterFault,
)


class SnowflakePostDataSourcesResponseAdapter(PostDataSourcesResponseAdapter):
    def _create_model_for_type(self, node_type: str, **kwargs) -> NodeResponseModel:
        """
        Method to create model object for a specific node type

        :param node_type: node type defining the model object
        :param kwargs:
        :return:
        """
        node_kwarg_name = "node"
        if node_kwarg_name not in kwargs:
            raise SagemakerSQLResponseAdapterFault(
                f"{self.__class__.__name__}"
                f'.{self._create_model_for_type.__name__}() function requires "{node_kwarg_name}" as keyword argument'
            )

        node_info = kwargs.get(node_kwarg_name)
        if node_type == NodeType.DATABASE.value.__str__():
            name = node_info[1]
            node_data = NodeDataModel(
                source=DataSourcesConstants.CONNECTION_TYPE_GLUE,
                type=DataSourceType.SNOWFLAKE.value.__str__(),
                sampleQuery=f"-- Query to list schemas from database '{name}'\n"
                f'SHOW SCHEMAS IN DATABASE "{name}"',
            )
        elif node_type == NodeType.SCHEMA.value.__str__():
            name = node_info[1]
            database_name = node_info[4]

            node_data = NodeDataModel(
                source=DataSourcesConstants.CONNECTION_TYPE_GLUE,
                type=DataSourceType.SNOWFLAKE.value.__str__(),
                sampleQuery=f"-- Query to list tables from schema '{database_name}.{name}'\n"
                f'SELECT * FROM "{database_name}"."INFORMATION_SCHEMA"."TABLES" WHERE TABLE_SCHEMA = \'{name}\' ORDER BY TABLE_TYPE ASC',
            )
        elif node_type == NodeType.TABLE.value.__str__():
            database_name = node_info[0]
            schema_name = node_info[1]
            name = node_info[2]

            # set table metadata considering "CreateTime" and "Owner" as optional fields
            table_metadata = {}
            if len(node_info) >= 5:
                table_metadata["Created On"] = convert_datetime_format(
                    node_info[4], "%b %d %Y %H:%M:%S %Z"
                )

            if len(node_info) >= 4:
                table_metadata["Owner"] = node_info[3]  # role name which owns the table

            node_data = TableNodeDataModel(
                source=DataSourcesConstants.CONNECTION_TYPE_GLUE,
                type=DataSourceType.SNOWFLAKE.value.__str__(),
                sampleQuery=f"-- Query to list columns in table '{database_name}.{schema_name}.{name}'\n"
                f'SELECT * FROM "{database_name}"."{schema_name}"."{name}"',
                tableMetadata=table_metadata,
            )
        elif node_type == NodeType.COLUMN.value.__str__():
            name = node_info[0]

            # parse column type
            column_type = node_info[1]

            node_data = ColumnNodeDataModel(
                source=DataSourcesConstants.CONNECTION_TYPE_GLUE,
                type=DataSourceType.SNOWFLAKE.value.__str__(),
                columnType=column_type,
            )
        else:
            raise SagemakerSQLResponseAdapterFault(f'node_type "{node_type}" not supported')

        return NodeResponseModel(
            name=name,
            nodeType=node_type,
            isLeaf=node_type == NodeType.COLUMN.value.__str__(),
            lastUpdateTime=current_time_utc().timestamp(),
            nodeData=node_data,
        )

    def _get_parent_node_type(self, child_node_type) -> str:
        """
        Method to get parent node type from child node type

        :param child_node_type: child node type
        :return:
        """
        if child_node_type == NodeType.DATABASE.value.__str__():
            return NodeType.DATA_SOURCE.value.__str__()
        elif child_node_type == NodeType.SCHEMA.value.__str__():
            return NodeType.DATABASE.value.__str__()
        elif child_node_type == NodeType.TABLE.value.__str__():
            return NodeType.SCHEMA.value.__str__()
        elif child_node_type == NodeType.COLUMN.value.__str__():
            return NodeType.TABLE.value.__str__()
        else:
            raise SagemakerSQLResponseAdapterFault(
                f'child_node_type "{child_node_type}" not supported'
            )
