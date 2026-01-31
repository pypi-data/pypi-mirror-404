# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from jupyter_server.extension.application import ExtensionApp

from amazon_sagemaker_sql_execution.utils.metrics.service_metrics import (
    initiate_logger,
    get_log_file_location,
)
from amazon_sagemaker_sql_editor.handlers import (
    ConnectionEntryHandler,
    ConnectionsHandler,
    DataSourcesDetailsHandler,
    DataSourcesAutocompleteHandler,
    SearchHandler,
)
from amazon_sagemaker_sql_editor.utils.constants import (
    SERVER_EXTENSION_APP_NAME,
    Api,
    AutocompleteApiConstants,
    LoggerDetails,
)


class SageMakerSQLExtensionApp(ExtensionApp):
    name = SERVER_EXTENSION_APP_NAME
    load_other_extensions = True
    handlers = [
        (rf"{Api.NAME_CONNECTIONS.value}", ConnectionsHandler),
        (rf"{Api.NAME_CONNECTION.value}/(.* ?)/?", ConnectionEntryHandler),
        (rf"{Api.NAME_DATA_SOURCES.value}", DataSourcesDetailsHandler),
        (
            rf"{Api.NAME_DATA_SOURCES_AUTOCOMPLETE.value}",
            DataSourcesAutocompleteHandler,
        ),
        (rf"{Api.NAME_SEARCH.value}", SearchHandler),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        initiate_logger(
            get_log_file_location(LoggerDetails.SAGEMAKER_SQL_EDITOR_LOG_FILE),
            LoggerDetails.LOGGER_NAME,
        )

    def initialize(self):
        """
        Initialize the extension app. The
        corresponding server app and webapp should already
        be initialized by this step.

        - calls super()
        - runs cache population task
        """
        super(SageMakerSQLExtensionApp, self).initialize()
        self._create_dirs_for_extension()

    def _create_dirs_for_extension(self):
        """
        Creates directories for storing server cache and autocomplete schema files
        :return: None
        """

        # Specify the directory paths
        autocomplete_schema_path = Path(f"{AutocompleteApiConstants.SCHEMA_DIR}")

        # Create the directories
        autocomplete_schema_path.mkdir(parents=True, exist_ok=True)
