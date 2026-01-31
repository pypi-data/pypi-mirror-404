import datetime
import inspect
import traceback
import logging

from amazon_sagemaker_sql_execution.utils.metrics.service_metrics import (
    stack_trace_filter,
    LogFileEnvironment,
    add_common_properties_to_metrics_context,
    CustomMetricsLogger,
    get_or_create_metrics_context,
    app_metadata,
)
from amazon_sagemaker_sql_execution.utils.metrics.app_metadata import JupyterLabEnvironment
from amazon_sagemaker_sql_execution.utils.constants import (
    SAGEMAKER_SQL_EXECUTION_LOG_BASE_DIRECTORY,
    METRICS_NAMESPACE,
)
from amazon_sagemaker_sql_editor.utils.constants import LoggerDetails, MetricsConstants
from amazon_sagemaker_sql_editor.utils.exceptions import (
    SagemakerSQLError,
    translate_exception,
)
from tornado import web
import botocore
from functools import wraps
import os


def get_log_file_location(log_file_name: str) -> str:
    home_dir = os.path.expanduser("~")
    log_file_path = os.path.join(home_dir, ".sagemaker")
    log_file_location = os.path.join(log_file_path, log_file_name)
    if app_metadata.sagemaker_environment == JupyterLabEnvironment.SAGEMAKER_STUDIO:
        os.makedirs(SAGEMAKER_SQL_EXECUTION_LOG_BASE_DIRECTORY, exist_ok=True)
        return os.path.join(SAGEMAKER_SQL_EXECUTION_LOG_BASE_DIRECTORY, log_file_name)
    os.makedirs(log_file_path, exist_ok=True)
    return log_file_location


def _extract_codes(exception):
    http_code = MetricsConstants.HTTP_SERVER_ERROR_CODE
    error_code = str(type(exception))
    if isinstance(exception, web.HTTPError):
        http_code = f"{exception.status_code}"
        error_code = exception.log_message.split(":")[0]
    elif isinstance(exception, botocore.exceptions.ClientError):
        error_code = f"{exception.response['Error']['Code']}"
        http_code = f"{exception.response['ResponseMetadata']['HTTPStatusCode']}"
    elif isinstance(exception, botocore.exceptions.EndpointConnectionError):
        error_code = "EndpointConnectionError"
        http_code = "503"

    return http_code, error_code


async def resolve_environment(logger_name):
    return LogFileEnvironment(logger_name)


def async_add_metrics(operation):
    def decorate(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.datetime.now()
            error = fault = 0
            http_code = MetricsConstants.HTTP_SUCCESS_CODE
            error_code = "None"
            success = 1

            context = get_or_create_metrics_context(args, func)
            metrics_logger = CustomMetricsLogger(
                LogFileEnvironment(LoggerDetails.LOGGER_NAME), context
            )
            # In case we're okay with adding a MetricsContext to the method signature, this decorator will set the value
            # for it so method/class specific metrics can be added
            if "metrics" in inspect.signature(func).parameters:
                kwargs["metrics"] = metrics_logger
            try:
                return await func(*args, **kwargs)
            except Exception as exception:
                exception = translate_exception(exception)
                http_code, error_code = _extract_codes(exception)
                if isinstance(exception, SagemakerSQLError):
                    error = 1
                else:
                    fault = 1
                    success = 0
                stack_trace = traceback.format_exc()
                context.set_property("StackTrace", stack_trace_filter.filter(stack_trace))
                raise exception
            finally:
                try:
                    context.namespace = METRICS_NAMESPACE
                    context.should_use_default_dimensions = False
                    context.put_dimensions({"Operation": operation})
                    add_common_properties_to_metrics_context(context)
                    context.set_property("HTTPResponseCode", http_code)
                    context.set_property("BotoErrorCode", error_code)
                    context.put_metric("Error", error, "Count")
                    context.put_metric("Fault", fault, "Count")
                    context.put_metric("Success", success, "Count")

                    elapsed = datetime.datetime.now() - start_time
                    context.put_metric(
                        "Latency", int(elapsed.total_seconds() * 1000), "Milliseconds"
                    )
                    metrics_logger.flush()
                except Exception as e:
                    logging.getLogger(LoggerDetails.LOGGER_NAME).error(
                        f"Exception when logging metrics {e}"
                    )

        return wrapper

    return decorate
