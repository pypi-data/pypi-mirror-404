# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import json

from amazon_sagemaker_sql_editor.utils.constants import SERVER_EXTENSION_APP_NAME
from amazon_sagemaker_sql_editor.extension import SageMakerSQLExtensionApp


def _jupyter_labextension_paths():
    HERE = Path(__file__).parent.resolve()

    with (HERE / "labextension" / "package.json").open(encoding="utf-8") as fid:
        package_json = json.load(fid)

    return [{"src": "labextension", "dest": package_json["name"]}]


def _jupyter_server_extension_points():
    """
    Returns a list of dictionaries with metadata describing
    where to find the `_load_jupyter_server_extension` function.
    """
    return [{"module": SERVER_EXTENSION_APP_NAME, "app": SageMakerSQLExtensionApp}]


def _load_jupyter_server_extension(server_app):
    """
    This function is called when the extension is loaded.
    """
    server_app.log.info("Loading SageMaker SQL Editor server extension")
    web_app = server_app.web_app
    base_url = web_app.settings["base_url"]


# For backward compatibility with notebook server - useful for Binder/JupyterHub
load_jupyter_server_extension = _load_jupyter_server_extension
