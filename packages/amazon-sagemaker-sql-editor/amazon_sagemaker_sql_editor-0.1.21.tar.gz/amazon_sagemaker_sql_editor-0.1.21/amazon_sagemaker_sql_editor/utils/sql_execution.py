# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
class SQLExecutionClient:
    """
    Async client for sql execution
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def __init__(self, metastore_id, metastore_type):
        self.metastore_id = metastore_id
        self.metastore_type = metastore_type
