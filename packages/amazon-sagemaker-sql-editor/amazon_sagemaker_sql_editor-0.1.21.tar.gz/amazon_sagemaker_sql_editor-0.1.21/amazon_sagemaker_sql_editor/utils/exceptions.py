# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import botocore.exceptions

from amazon_sagemaker_sql_execution.utils.metrics.app_metadata import (
    get_sagemaker_image,
)


SAGEMAKER_DISTRIBUTION = "sagemaker-distribution"


def translate_exception(exception):
    """
    Translate known compatibility issues to appropriate SageMaker SQL exceptions
    """
    if (
        isinstance(exception, AttributeError)
        and "_get_ignored_credentials" in str(exception)
        and SAGEMAKER_DISTRIBUTION not in get_sagemaker_image()
    ):  # so we are not blind to issues in SMD
        # Set __cause__ to preserve original exception chain
        # https://stackoverflow.com/questions/54768239/in-python-how-do-i-construct-an-exception-from-another-exception-without-raisin
        new_exception = SagemakerSQLApiServiceError(
            "Version compatibility issue detected. Please ensure aiobotocore and botocore versions are compatible."
        )
        new_exception.__cause__ = exception
        return new_exception
    return exception


class SageMakerSQLExceptionFactory:
    """
    Returns appropriate subclass of exception to raise
    """

    @staticmethod
    def get_sql_exception(error):
        """
        Returns appropriate subclass of exception. Defaults to SagemakerSQLFault

        :param error:
        :return:
        """

        if isinstance(error, botocore.exceptions.ClientError):
            return SageMakerSQLExceptionFactory.get_exception_from_boto_client_error(error)
        elif isinstance(error, botocore.exceptions.ConnectTimeoutError):
            helpful_context = "Connection timed out. Looks like you do not have required networking setup to connect with AWS services. Please follow this guide to get it fixed, https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-sql-extension-networking.html."
            return ConnectionTimeoutError(f"{helpful_context} Error message: {error}")
        else:
            return SagemakerSQLFault(error)

    @staticmethod
    def get_exception_from_boto_client_error(error: botocore.exceptions.ClientError):
        boto_error_code = error.response["Error"]["Code"]
        boto_error_message = error.response["Error"]["Message"]
        base_error_message = f"{boto_error_code}: {boto_error_message}"
        if boto_error_code == "AccessDeniedException":
            helpful_context = "For more information, refer to https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-sql-extension-datasources-connection-permissions.html."
            return AccessDeniedError(f"{base_error_message}. {helpful_context}")
        elif boto_error_code == "EntityNotFound":
            return EntityNotFoundError(error)
        elif boto_error_code == "OperationTimeoutException":
            return OperationTimeoutError(error)
        elif boto_error_code == "AlreadyExistsException":
            return DuplicateResourceException(error)
        elif boto_error_code == "EntityNotFoundException":
            return ResourceNotFoundException(error)
        elif boto_error_code == "InvalidInputException":
            return InvalidInputException(error.response["Error"]["Message"])
        else:
            return SagemakerSQLFault(error)


class SagemakerSQLError(Exception):
    """
    Generic exception that is the base exception for all other Errors from this lib
    """

    pass


class SagemakerSQLFault(Exception):
    """
    Generic exception that is the base exception for all other Faults from this lib
    """

    pass


class AccessDeniedError(SagemakerSQLError):
    """
    Encapsulate Exceptions for this lib
    """

    pass


class EntityNotFoundError(SagemakerSQLError):
    """
    Encapsulate Exceptions for this lib
    """

    pass


class OperationTimeoutError(SagemakerSQLError):
    """
    Encapsulate Exceptions for this lib
    """

    pass


class ConnectionTimeoutError(SagemakerSQLError):
    """
    Encapsulate Exceptions for this lib
    """

    pass


class SagemakerSQLResponseAdapterFault(SagemakerSQLFault):
    """
    Fault thrown during response adapter operations
    """

    pass


class SagemakerSQLDataProviderServiceFault(SagemakerSQLFault):
    """
    Fault thrown during data provider service operations
    """

    pass


class SagemakerSQLDataProviderServiceError(SagemakerSQLError):
    """
    Error thrown during data provider service operations
    """

    pass


class SagemakerSQLApiServiceFault(SagemakerSQLFault):
    """
    Fault thrown during api service operations
    """

    pass


class SagemakerSQLApiServiceError(SagemakerSQLError):
    """
    Error thrown during api service operations
    """

    pass


class SagemakerSQLApiHandlerFault(SagemakerSQLFault):
    """
    Fault thrown during api handler operations
    """

    pass


class SagemakerSQLApiHandlerError(SagemakerSQLError):
    """
    Error thrown during api handler operations
    """

    pass


class SagemakerSQLPaginationError(SagemakerSQLError):
    """
    Error thrown during pagination operations
    """

    pass


class SagemakerSQLPaginationFault(SagemakerSQLFault):
    """
    Fault thrown during pagination operations
    """

    pass


class DuplicateResourceException(Exception):
    """
    Encapsulate Exceptions for this lib
    """

    pass


class ResourceNotFoundException(Exception):
    """
    Encapsulate Exceptions for this lib
    """

    pass


class InvalidInputException(Exception):
    """
    Encapsulate Exceptions for this lib
    """

    pass
