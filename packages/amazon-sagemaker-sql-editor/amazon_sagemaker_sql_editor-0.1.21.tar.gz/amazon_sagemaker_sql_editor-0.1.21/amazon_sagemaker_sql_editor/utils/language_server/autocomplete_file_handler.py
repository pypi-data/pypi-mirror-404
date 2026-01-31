import json
import shutil
from urllib.request import pathname2url, url2pathname

from amazon_sagemaker_sql_editor.utils.constants import (
    AutocompleteApiConstants,
    DataSourcesApiResponse,
)


class AutocompleteSchemaFileHandler:
    """
    Helper class to manage files containing connection schemas for autocompletion capability.
    The schema files are required by sql-language-server to parse information for serving
    autocomplete suggestions.
    """

    @classmethod
    def update_connection_schema_file(cls, connection_name: str, connection_schema: dict):
        """
        Saves connection-level schema file at pre-defined path

        :param connection_name: name of the connection to create file name
        :param connection_schema: schema of the connection for file content
        """
        cls._save_file(
            directory=AutocompleteApiConstants.SCHEMA_DIR,
            filename=f"{connection_name}.json",
            file_content=json.dumps(connection_schema, indent=2),
        )

    @classmethod
    def update_central_schema_file(cls, connection_name: str = None):
        """
        Copies connection-level schema file to central schema file. Clears the content of central schema file
        if no connection name is provided.

        Central schema file has a static name and path.

        :param connection_name: name of the connection to copy file from
        """

        # if connection name is provided, overwrite central schema file with connection-level schema file
        if connection_name:
            connection_schema_filepath = (
                f"{AutocompleteApiConstants.SCHEMA_DIR}/{cls._encode_text(connection_name)}.json"
            )
            central_schema_filepath = f"{AutocompleteApiConstants.SCHEMA_DIR}/{AutocompleteApiConstants.CENTRAL_SCHEMA_FILENAME}"
            shutil.copy(connection_schema_filepath, central_schema_filepath)
        else:
            # if connection name is None, overwrite with empty schema
            cls._save_file(
                directory=AutocompleteApiConstants.SCHEMA_DIR,
                filename=AutocompleteApiConstants.CENTRAL_SCHEMA_FILENAME,
                file_content="{}",
            )

    @classmethod
    def get_connection_schema_from_file(cls, connection_name: str):
        """
        Reads connection-level schema file and returns file contents as json.

        :param connection_name: name of the connection to read file
        """
        try:
            connection_schema_filepath = (
                f"{AutocompleteApiConstants.SCHEMA_DIR}/{cls._encode_text(connection_name)}.json"
            )
            with open(connection_schema_filepath, "r") as file:
                file_content = json.loads(file.read())
        except FileNotFoundError:
            # file doesn't exist; suppress the error
            return None
        return file_content

    @classmethod
    def _save_file(cls, directory: str, filename: str, file_content: str):
        """
        Reads file based on parameters provided
        """
        if not filename.__contains__("."):
            raise ValueError("filename should be provided with extension")

        # url-encode file to avoid any errors by the presence of special characters in filename
        filename = cls._encode_text(filename)
        try:
            with open(f"{directory}/{filename}", "w") as file:
                file.write(file_content)
        except Exception:
            # Swallowing exception because we are supporting autocomplete only from Sagemaker distribution image 1.7.1
            return None

    @classmethod
    def _read_file(cls, directory: str, filename: str, file_ext: str) -> str:
        filename = cls._encode_text(filename)
        with open(f"{directory}/{filename}.{file_ext}", "r") as file:
            file_content = file.read()
        return file_content

    @staticmethod
    def _encode_text(raw_text: str):
        """
        Function to URL-encode a string
        :param raw_text: raw text to be encoded
        :return: URL-encoded string
        """
        return pathname2url(raw_text)

    @classmethod
    def is_connection_schema_file_updated(cls, connection_name: str, last_modified: float) -> bool:
        """
        Function to check if the connection schema file's last update timestamp is older or as recent as a
        given timestamp.

        :param connection_name: name of the connection to pull connection schema file
        :param last_modified: timestamp to compare recency
        :return: bool: returns false if the file is stale
        """
        connection_schema = cls.get_connection_schema_from_file(connection_name)
        # case when file does not exist or no schema exists
        if connection_schema is None or connection_schema == {}:
            return False
        else:
            return connection_schema[DataSourcesApiResponse.LAST_UPDATE_TIME_KEY] >= last_modified
