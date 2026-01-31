from amazon_sagemaker_sql_editor.utils.constants import DataSourcesApiResponse


class AutocompleteSchemaAdapter:
    @staticmethod
    def adapt_to_language_server_format(response_schema: dict):
        tables = []
        for catalog in response_schema[DataSourcesApiResponse.NODE_LIST_KEY]:
            catalog_name = catalog[DataSourcesApiResponse.NAME_KEY]
            for database in catalog[DataSourcesApiResponse.NODE_LIST_KEY]:
                database_name = database[DataSourcesApiResponse.NAME_KEY]
                for table in database[DataSourcesApiResponse.NODE_LIST_KEY]:
                    table_name = table[DataSourcesApiResponse.NAME_KEY]
                    columns = []
                    for column in table[DataSourcesApiResponse.NODE_LIST_KEY]:
                        column_name = column[DataSourcesApiResponse.NAME_KEY]
                        columns.append({"columnName": column_name})

                    tables.append(
                        {
                            "tableName": table_name,
                            "columns": columns,
                            "database": database_name,
                            "catalog": catalog_name,
                        }
                    )

        return {
            "tables": tables,
            "functions": [],
            f"{DataSourcesApiResponse.LAST_UPDATE_TIME_KEY}": response_schema[
                DataSourcesApiResponse.LAST_UPDATE_TIME_KEY
            ],
        }
