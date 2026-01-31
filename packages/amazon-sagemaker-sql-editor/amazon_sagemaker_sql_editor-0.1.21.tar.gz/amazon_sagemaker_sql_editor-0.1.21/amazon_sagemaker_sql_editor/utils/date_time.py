# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import datetime


def current_time_utc() -> datetime.datetime:
    return datetime.datetime.utcnow()


def convert_datetime_format(dt: datetime, format: str) -> str:
    """
    Functions which converts a datetime object to a string of desired format.
    Format codes reference: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

    :param dt: datetime object to convert
    :param format: datetime format to convert
    :return: string in desired datetime format
    """
    if dt:
        return f"{dt:{format}}"
    else:
        # Information schema has views which don't have created timestamp.
        return ""
