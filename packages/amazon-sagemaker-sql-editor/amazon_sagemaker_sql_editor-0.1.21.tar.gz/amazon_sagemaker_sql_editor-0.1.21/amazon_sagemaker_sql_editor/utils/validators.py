# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

from amazon_sagemaker_sql_editor.utils.constants import GlueConnectionType
from amazon_sagemaker_sql_editor.utils.exceptions import InvalidInputException

athena_connection_supported_properties = [
    "work_group",
    "s3_staging_dir",
    "schema_name",
    "catalog_name",
    "encryption_option",
    "kms_key",
    "aws_secret_arn",
    "poll_interval",
    "result_reuse_enable",
    "result_reuse_minutes",
    "duration_seconds",
]

redshift_connection_supported_properties = [
    "database",
    "port",
    "cluster_identifier",
    "host",
    "serverless_work_group",
    "serverless_acct_id",
    "aws_secret_arn",
    "auto_create",
    "db_groups",
    "ssl",
    "sslmode",
    "database_metadata_current_db_only",
    "max_prepared_statements",
    "numeric_to_float",
    "timeout",
]

snowflake_connection_supported_properties = [
    "account",
    "database",
    "schema",
    "warehouse",
    "login_timeout",
    "network_timeout",
    "client_prefetch_threads",
    "validate_default_parameters",
    "arrow_number_to_decimal",
    "autocommit",
    "aws_secret_arn",
]


def validate_connection_input(
    name: str,
    description: str,
    connection_type: str,
    connection_properties: str,
):
    if not name:
        raise InvalidInputException("Required parameter missing: Name")
    if not description:
        raise InvalidInputException("Required parameter missing: Description")
    if not connection_type:
        raise InvalidInputException("Required parameter missing: ConnectionType")
    if not connection_properties:
        raise InvalidInputException("Required parameter missing: ConnectionProperties")

    if connection_type not in [member.value.__str__() for member in GlueConnectionType]:
        raise InvalidInputException(f"Invalid Connection Type: {connection_type}")
    validate_connection_properties(
        connection_type=connection_type,
        connection_properties=connection_properties,
    )


def validate_connection_properties(connection_type: str, connection_properties: str):
    if "PythonProperties" not in connection_properties:
        raise InvalidInputException(
            "Required parameter missing: PythonProperties in ConnectionProperties"
        )
    python_properties = json.loads(connection_properties["PythonProperties"])

    if connection_type == GlueConnectionType.ATHENA.value.__str__():
        validate_athena_connection_properties(python_properties=python_properties)
    elif connection_type == GlueConnectionType.REDSHIFT.value.__str__():
        validate_redshift_connection_properties(python_properties=python_properties)
    elif connection_type == GlueConnectionType.SNOWFLAKE.value.__str__():
        validate_snowflake_connection_properties(python_properties=python_properties)


def validate_athena_connection_properties(python_properties: dict):
    validate_supported_connection_properties(
        python_properties, athena_connection_supported_properties
    )
    s3_staging_dir = None
    if "s3_staging_dir" in python_properties:
        s3_staging_dir = python_properties["s3_staging_dir"]
    work_group = None
    if "work_group" in python_properties:
        work_group = python_properties["work_group"]
    if not s3_staging_dir and not work_group:
        raise InvalidInputException("Must enter either workgroup, or S3 staging directory")


def validate_redshift_connection_properties(python_properties: dict):
    validate_supported_connection_properties(
        python_properties, redshift_connection_supported_properties
    )


def validate_snowflake_connection_properties(python_properties: dict):
    validate_supported_connection_properties(
        python_properties, snowflake_connection_supported_properties
    )
    if not "account" in python_properties or not python_properties["account"]:
        raise InvalidInputException("Required parameter missing: Account")


def validate_supported_connection_properties(python_properties: dict, supported_properties: list):
    for python_property in python_properties:
        if python_property not in supported_properties:
            raise InvalidInputException(f"Property not supported: {python_property}")
