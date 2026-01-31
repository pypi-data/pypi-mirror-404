# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from amazon_sagemaker_sql_editor.utils.constants import (
    NodeType,
    DataSourceType,
    DataSourcesConstants,
)
from amazon_sagemaker_sql_editor.utils.date_time import (
    current_time_utc,
    convert_datetime_format,
)

from amazon_sagemaker_sql_editor.model.models import (
    DataSourcesNodeResponseModel as NodeResponseModel,
    DataSourcesNodeDataModel as NodeDataModel,
    DataSourcesTableNodeDataModel as TableNodeDataModel,
    DataSourcesColumnNodeDataModel as ColumnNodeDataModel,
)
from amazon_sagemaker_sql_editor.adapter.adapters import PostDataSourcesResponseAdapter
from amazon_sagemaker_sql_editor.utils.exceptions import (
    SagemakerSQLResponseAdapterFault,
)


class AthenaPostDataSourcesResponseAdapter(PostDataSourcesResponseAdapter):
    def _create_model_for_type(self, node_type: str, **kwargs) -> NodeResponseModel:
        """
        TODO: If-else ladder is hard to maintain and involves a lot of code duplication (in each adapter).
        TODO: Consider using: https://refactoring.guru/design-patterns/chain-of-responsibility pattern.

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
        if node_type == NodeType.DATA_SOURCE.value.__str__():
            name = node_info["CatalogName"]
            node_data = NodeDataModel(
                source=DataSourcesConstants.CONNECTION_TYPE_GLUE,
                type=DataSourceType.ATHENA.value.__str__(),
                sampleQuery=f"-- Query to list schemas in data-source '{name}'\n"
                f"SELECT schema_name AS database_name "
                f"FROM information_schema.schemata "
                f"WHERE schema_name <> 'information_schema' "
                f"AND catalog_name = '{str(name).lower()}'",
            )
        elif node_type == NodeType.DATABASE.value.__str__():
            name = node_info["Name"]
            node_data = NodeDataModel(
                source=DataSourcesConstants.CONNECTION_TYPE_GLUE,
                type=DataSourceType.ATHENA.value.__str__(),
                sampleQuery=f"-- Query to list tables in database '{name}'\n"
                f"SHOW TABLES IN `{name}`",
            )
        elif node_type == NodeType.TABLE.value.__str__():
            name = node_info["Name"]
            catalog_name = node_info["CatalogName"]
            database_name = node_info["DatabaseName"]

            # set table metadata considering "CreateTime" as an optional field
            table_metadata = {}
            if "CreateTime" in node_info:
                table_metadata["Created On"] = convert_datetime_format(
                    node_info["CreateTime"], "%b %d %Y %H:%M:%S %Z"
                )

            node_data = TableNodeDataModel(
                source=DataSourcesConstants.CONNECTION_TYPE_GLUE,
                type=DataSourceType.ATHENA.value.__str__(),
                sampleQuery=f"-- Query to list columns in table '{catalog_name}.{database_name}.{name}'\n"
                f'SELECT * FROM "{catalog_name}"."{database_name}"."{name}"',
                tableMetadata=table_metadata,
            )
        elif node_type == NodeType.COLUMN.value.__str__():
            name = node_info["Name"]
            node_data = ColumnNodeDataModel(
                source=DataSourcesConstants.CONNECTION_TYPE_GLUE,
                type=DataSourceType.ATHENA.value.__str__(),
                columnType=node_info["Type"],
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

        if child_node_type == NodeType.DATA_SOURCE.value.__str__():
            return NodeType.DATA_SOURCE.value.__str__()
        elif child_node_type == NodeType.DATABASE.value.__str__():
            return NodeType.DATA_SOURCE.value.__str__()
        elif child_node_type == NodeType.TABLE.value.__str__():
            return NodeType.DATABASE.value.__str__()
        elif child_node_type == NodeType.COLUMN.value.__str__():
            return NodeType.TABLE.value.__str__()
        else:
            raise SagemakerSQLResponseAdapterFault(
                f'child_node_type "{child_node_type}" not supported'
            )
