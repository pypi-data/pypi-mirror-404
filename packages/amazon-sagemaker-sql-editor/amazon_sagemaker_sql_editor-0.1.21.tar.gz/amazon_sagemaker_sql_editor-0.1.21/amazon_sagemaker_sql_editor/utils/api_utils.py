# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os
from typing import List

from amazon_sagemaker_sql_editor.utils.constants import PathEnum


class PathHelper:
    """
    Class providing helper functions related to 'path' parameter for POST./api/data-sources
    """

    @staticmethod
    def get_path_components(path: str) -> List[str]:
        """
        Splits path into a list using "/" as a delimiter
        :param path: path parameter to split
        :return: list of path components
        """
        return path.strip().split(PathEnum.DELIMITER)

    @staticmethod
    def is_root_path(path: str) -> bool:
        """
        Checks if path is at root level or not

        :param path: path to check
        :return: bool indicating whether path is root
        """
        return path.strip() == PathEnum.ROOT


class SageMakerUtils:
    @staticmethod
    def is_sagemaker_environment() -> bool:
        """Determines if this is SageMaker environment

        # This is a public contract -
        https://docs.aws.amazon.com/sagemaker/latest/dg/notebooks-run-and-manage-metadata.html

        :return:
        """
        return os.path.exists("/opt/ml/metadata/resource-metadata.json")
