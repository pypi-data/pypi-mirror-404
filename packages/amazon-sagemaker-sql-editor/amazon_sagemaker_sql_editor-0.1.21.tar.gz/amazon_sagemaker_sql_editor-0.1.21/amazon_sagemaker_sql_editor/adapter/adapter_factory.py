# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from amazon_sagemaker_sql_editor.utils.constants import DataSourceType
from amazon_sagemaker_sql_editor.data_store.glue.adapter import (
    GlueGetConnectionsResponseAdapter,
    GluePostDataSourcesResponseAdapter,
)
from amazon_sagemaker_sql_editor.data_store.athena.adapter import (
    AthenaPostDataSourcesResponseAdapter,
)
from amazon_sagemaker_sql_editor.data_store.redshift.adapter import (
    RedshiftPostDataSourcesResponseAdapter,
)
from amazon_sagemaker_sql_editor.data_store.snowflake.adapter import (
    SnowflakePostDataSourcesResponseAdapter,
)
from amazon_sagemaker_sql_editor.adapter.adapters import (
    GetConnectionsResponseAdapter,
    PostDataSourcesResponseAdapter,
)

from amazon_sagemaker_sql_editor.utils.exceptions import (
    SagemakerSQLResponseAdapterFault,
)

# TODO: This if-else ladder can be replaced with responds_to method present in ResponseAdapter parent class.
#  We can dynamically identify the sub-classes for this class (computed only once), making the Factory generic.
#  Ref: https://code.amazon.com/packages/SMUnoSQLExecution/blobs/mainline/--/sagemaker_sql_execution/src/sagemaker_sql_execution/utils/sql_connection_supplier_factory.py


class GetConnectionsResponseAdapterFactory:
    def get_adapter(self, data_source_type: DataSourceType) -> type(GetConnectionsResponseAdapter):
        if data_source_type == DataSourceType.GLUE:
            return GlueGetConnectionsResponseAdapter
        else:
            raise SagemakerSQLResponseAdapterFault(
                f'data_source_type "{data_source_type}" not supported'
            )


class PostDataSourcesResponseAdapterFactory:
    def get_adapter(self, data_source_type: str) -> type(PostDataSourcesResponseAdapter):
        if data_source_type == DataSourceType.ATHENA.value.__str__():
            return AthenaPostDataSourcesResponseAdapter
        elif data_source_type == DataSourceType.REDSHIFT.value.__str__():
            return RedshiftPostDataSourcesResponseAdapter
        elif data_source_type == DataSourceType.SNOWFLAKE.value.__str__():
            return SnowflakePostDataSourcesResponseAdapter
        elif data_source_type == DataSourceType.GLUE.value.__str__():
            return GluePostDataSourcesResponseAdapter
        else:
            raise SagemakerSQLResponseAdapterFault(
                f'data_source_type "{data_source_type}" not supported'
            )
