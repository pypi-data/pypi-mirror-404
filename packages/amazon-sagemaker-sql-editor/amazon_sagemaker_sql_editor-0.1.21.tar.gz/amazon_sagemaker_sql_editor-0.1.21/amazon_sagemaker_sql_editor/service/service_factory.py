# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from amazon_sagemaker_sql_editor.utils.constants import DataSourceType
from amazon_sagemaker_sql_editor.service.data_provider_service import (
    BaseDataProviderService,
)
from amazon_sagemaker_sql_editor.data_store.athena.service import (
    AthenaDataProviderService,
)
from amazon_sagemaker_sql_editor.data_store.redshift.service import (
    RedshiftDataProviderService,
)
from amazon_sagemaker_sql_editor.data_store.snowflake.service import (
    SnowflakeDataProviderService,
)

from amazon_sagemaker_sql_editor.utils.exceptions import (
    SagemakerSQLDataProviderServiceFault,
)


class DataProviderServiceFactory:
    def create_service(self, data_provider_type: str) -> type(BaseDataProviderService):
        if data_provider_type == DataSourceType.ATHENA.value.__str__():
            return AthenaDataProviderService
        elif data_provider_type == DataSourceType.REDSHIFT.value.__str__():
            return RedshiftDataProviderService
        elif data_provider_type == DataSourceType.SNOWFLAKE.value.__str__():
            return SnowflakeDataProviderService
        else:
            raise SagemakerSQLDataProviderServiceFault("Unsupported data provider")
