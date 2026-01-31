# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import List

from amazon_sagemaker_sql_editor.service.data_provider_service import (
    SQLDataProviderService,
)

from amazon_sagemaker_sql_editor.utils.constants import NodeType
from amazon_sagemaker_sql_editor.utils.exceptions import (
    SagemakerSQLDataProviderServiceFault,
)


class SnowflakeDataProviderService(SQLDataProviderService):
    """
    Class to fetch data stored in Snowflake
    """

    def __init__(self, connection_name: str, path_components: List[str], metastore_type: str):
        super().__init__(
            connection_name=connection_name,
            path_components=path_components,
            metastore_type=metastore_type,
        )
        self.fully_qualified_sql_path = ".".join(['"' + s + '"' for s in self.path_components[1:]])

    async def _get_databases(self, **kwargs):
        sql_query = "SHOW DATABASES"
        return await self._get_query_results(sql_query=sql_query)

    async def _get_schemas(self, **kwargs):
        sql_query = f"SHOW SCHEMAS IN DATABASE {self.fully_qualified_sql_path}"
        return await self._get_query_results(sql_query=sql_query)

    async def _get_data_catalogs(self, **kwargs):
        raise NotImplementedError()

    async def _get_tables(self, **kwargs):
        database_name = self.path_components[1]
        schema_name = self.path_components[2]
        sql_query = (
            f"SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, TABLE_OWNER, CREATED, * "
            f'FROM "{database_name}"."INFORMATION_SCHEMA"."TABLES" '
            f"WHERE TABLE_SCHEMA like '{schema_name}' ORDER BY TABLE_TYPE ASC"
        )
        return await self._get_query_results(sql_query=sql_query)

    async def _get_columns(self, **kwargs):
        sql_query = f"DESC TABLE {self.fully_qualified_sql_path}"
        return await self._get_query_results(sql_query=sql_query)

    async def _get_data_at_path(self) -> dict:
        """
        1. Determines data hierarchy depth using self.path_components
        2. Calls relevant method to fetch data based on data hierarchy depth
        3. Returns fetched data in a standard format
        :return:
        """
        data_hierarchy_depth = len(self.path_components)
        if data_hierarchy_depth == 1:
            return {
                "nodes": await self._get_databases(),
                "nodesType": NodeType.DATABASE.value.__str__(),
            }
        elif data_hierarchy_depth == 2:
            return {
                "nodes": await self._get_schemas(),
                "nodesType": NodeType.SCHEMA.value.__str__(),
            }
        elif data_hierarchy_depth == 3:
            return {
                "nodes": await self._get_tables(),
                "nodesType": NodeType.TABLE.value.__str__(),
            }
        elif data_hierarchy_depth == 4:
            return {
                "nodes": await self._get_columns(),
                "nodesType": NodeType.COLUMN.value.__str__(),
            }
        else:
            raise SagemakerSQLDataProviderServiceFault(
                f"Unsupported data hierarchy depth for {self.__class__.__name__}"
            )
