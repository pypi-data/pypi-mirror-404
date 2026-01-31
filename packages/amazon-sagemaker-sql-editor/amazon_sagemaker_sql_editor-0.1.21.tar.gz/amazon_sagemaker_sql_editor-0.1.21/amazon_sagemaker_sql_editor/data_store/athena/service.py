# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from typing import Optional, List

from amazon_sagemaker_sql_editor.utils.constants import NodeType
from amazon_sagemaker_sql_editor.service.data_provider_service import (
    BotoDataProviderService,
)

from amazon_sagemaker_sql_editor.utils.exceptions import (
    SagemakerSQLDataProviderServiceFault,
)


class AthenaDataProviderService(BotoDataProviderService):
    """
    Class to fetch data stored in Athena
    """

    def __init__(self, connection_name: str, path_components: List[str], metastore_type: str):
        super().__init__(
            connection_name=connection_name,
            path_components=path_components,
            metastore_type=metastore_type,
        )
        self.service_client_args = {"service_name": "athena"}
        self.service_client_fault_codes = [
            "InternalServerException",
            "MetadataException",
        ]
        self.service_client_error_codes = ["InvalidRequestException"]

    async def _fetch_all(
        self,
        boto_client_api: str,
        boto_response_list_key,
        catalog_name: Optional[str] = None,
        database_name: Optional[str] = None,
        table_name: Optional[str] = None,
    ):
        """
        Fetches all the data for 'boto_client_api' by paginating over the result set of the Boto API.
        See: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html

        :param boto_response_list_key: Athena Boto API response object's key holding the list of page items
        :param boto_client_api: Athena Boto API which provides the data
        :param catalog_name: Athena catalog name
        :param database_name: Athena database name
        :param table_name: Athena table name
        :return: object combining all pages of data returned through Boto APIs
        """

        paginator = self.service_client.get_paginator(boto_client_api)

        paginate_args = {}
        if catalog_name:
            paginate_args.update({"CatalogName": catalog_name})
        if database_name:
            paginate_args.update({"DatabaseName": database_name})
        if table_name:
            paginate_args.update({"Expression": table_name})
        page_iterator = paginator.paginate(**paginate_args)

        result = {boto_response_list_key: []}
        for page in page_iterator:
            page = await page
            result[boto_response_list_key].extend(page[boto_response_list_key])
        return result

    async def _get_databases(self, **kwargs):
        catalog_name = self.path_components[1]
        boto_response_list_key = "DatabaseList"
        database_list = await self._fetch_all(
            "list_databases",
            boto_response_list_key=boto_response_list_key,
            catalog_name=catalog_name,
        )
        return database_list[boto_response_list_key]

    async def _get_schemas(self, **kwargs):
        raise NotImplementedError()

    async def _get_data_catalogs(self, **kwargs):
        boto_response_list_key = "DataCatalogsSummary"
        catalogs_summary = await self._fetch_all(
            "list_data_catalogs", boto_response_list_key=boto_response_list_key
        )
        return catalogs_summary[boto_response_list_key]

    async def _get_tables(self, **kwargs):
        catalog_name = self.path_components[1]
        database_name = self.path_components[2]
        boto_response_list_key = "TableMetadataList"
        table_list = await self._fetch_all(
            "list_table_metadata",
            boto_response_list_key=boto_response_list_key,
            catalog_name=catalog_name,
            database_name=database_name,
        )

        # add catalog name and database name in each table's info
        for table_info in table_list[boto_response_list_key]:
            table_info.update({"CatalogName": catalog_name, "DatabaseName": database_name})

        return table_list[boto_response_list_key]

    async def _get_columns(self, **kwargs):
        table_name = self.path_components[3]
        table_list = await self._get_tables()

        for table_data in table_list:
            if table_data["Name"] == table_name:
                return table_data["Columns"]

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
                "nodes": await self._get_data_catalogs(),
                "nodesType": NodeType.DATA_SOURCE.value.__str__(),
            }
        elif data_hierarchy_depth == 2:
            return {
                "nodes": await self._get_databases(),
                "nodesType": NodeType.DATABASE.value.__str__(),
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
