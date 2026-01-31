# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os
import botocore.client
from aiobotocore.session import get_session

from amazon_sagemaker_sql_editor.utils.constants import ClientType, USE_DUALSTACK_ENDPOINT
from amazon_sagemaker_sql_editor.utils.sql_execution import SQLExecutionClient

from amazon_sagemaker_sql_editor.utils.exceptions import SagemakerSQLFault


class ClientFactory:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _get_region(self):
        # region is set as env var in Studio
        return os.environ["AWS_REGION"]

    def create_client(self, client_type: ClientType, client_args: dict):
        if client_type == ClientType.BOTO:
            return self._create_boto_client(client_args)
        elif client_type == ClientType.SQL:
            return self._create_sql_execution_client(client_args)
        else:
            raise NotImplementedError()

    def _create_boto_client(self, client_args):
        if "config" not in client_args:
            client_args["config"] = botocore.client.Config(
                connect_timeout=10,
                read_timeout=20,
                retries={"max_attempts": 1},
                use_dualstack_endpoint=USE_DUALSTACK_ENDPOINT,
            )
        if "region_name" not in client_args:
            client_args["region_name"] = self._get_region()
        return get_session().create_client(**client_args)

    def _create_sql_execution_client(self, client_args):
        if "metastore_id" not in client_args:
            raise SagemakerSQLFault(
                'Key "metastore_id" must be present for sql execution client creation'
            )
        if "metastore_type" not in client_args:
            raise SagemakerSQLFault(
                'Key "metastore_type" must be present for sql execution client creation'
            )

        return SQLExecutionClient(**client_args)
