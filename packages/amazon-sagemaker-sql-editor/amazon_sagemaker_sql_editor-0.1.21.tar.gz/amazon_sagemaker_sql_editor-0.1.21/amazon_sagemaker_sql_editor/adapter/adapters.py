# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import dataclasses
from typing import Optional

from amazon_sagemaker_sql_editor.model.models import (
    ConnectionsResponseModel,
    DataSourcesNodeResponseModel as NodeResponseModel,
)
from amazon_sagemaker_sql_editor.utils.date_time import current_time_utc
from amazon_sagemaker_sql_editor.utils.exceptions import (
    SagemakerSQLResponseAdapterFault,
)


# TODO: Consider getting rid of _set_model() code and initializing model in __init__()


class BaseResponseAdapter:
    """
    Base adapter class to convert data into a standard format for server response
    """

    def __init__(self, **kwargs):
        self.model = None  # Model object to store data for server response

    def _set_model(self, **kwargs):
        """
        TODO: Consider changing method signature by removing generic to specific arg names

        Method to create and set response-model object using data received from service clients

        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def convert_model_to_dict(self) -> dict:
        """
        Method to convert model object into dict as required for server response
        :return:
        """
        return dataclasses.asdict(
            self.model, dict_factory=lambda x: {k: v for (k, v) in x if v is not None}
        )


class GetConnectionsResponseAdapter(BaseResponseAdapter):
    """
    Adapter class to convert data into a standard format for server response for the api: GET./api/connections
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model: Optional[ConnectionsResponseModel] = (
            None  # Model object to store data for server response
        )

    def _set_model(self, **kwargs):
        """
        Method to create and set response-model object using data received from service clients. The response-model
        pertains to the api: GET./api/connections.

        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def convert_model_to_dict(self) -> dict:
        """
        Method to convert model object into dict as required for server response for the api: GET./api/connections.
        :return:
        """
        return super().convert_model_to_dict()

    def filter_response(self, connection_type: str):
        if self.model is None:
            raise ValueError(f'"model" cannot be of NoneType')

        if not isinstance(self.model, ConnectionsResponseModel):
            raise SagemakerSQLResponseAdapterFault(
                f'"model" needs to be of type {ConnectionsResponseModel.__class__.__name__}'
            )

        self.model.connections = list(
            filter(lambda c: c.type == connection_type, self.model.connections)
        )


class PostDataSourcesResponseAdapter(BaseResponseAdapter):
    """
    Adapter class to convert data into a standard format for server response for the api: POST./api/data-sources
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model: Optional[NodeResponseModel] = (
            None  # Model object to store data for server response
        )
        self._set_model(**kwargs)

    def _set_model(self, **kwargs):
        """
        Method to create and set response-model object using data received from service clients. The response-model
        pertains to the api: POST./api/data-sources.

        :param kwargs:
        :return:
        """
        nodes_kwarg_name = "nodes"
        if nodes_kwarg_name not in kwargs:
            raise SagemakerSQLResponseAdapterFault(
                f"{self.__class__.__name__}"
                f'.{self._set_model.__name__}() function requires "{nodes_kwarg_name}" as keyword argument'
            )

        nodes_type_kwarg_name = "nodesType"
        if nodes_type_kwarg_name not in kwargs:
            raise SagemakerSQLResponseAdapterFault(
                f"{self.__class__.__name__}"
                f'.{self._set_model.__name__}() function requires "{nodes_type_kwarg_name}" as keyword argument'
            )

        nodes = kwargs.get(nodes_kwarg_name)
        nodes_type = kwargs.get(nodes_type_kwarg_name)
        node_list = []
        for node in nodes:
            node_model = self._create_model_for_type(node_type=nodes_type, node=node)
            node_list.append(node_model)

        model = NodeResponseModel(
            isLeaf=False,
            lastUpdateTime=current_time_utc().timestamp(),
            nodeList=node_list,
            nodeType=self._get_parent_node_type(child_node_type=nodes_type),
        )

        self.model = model

    def convert_model_to_dict(self) -> dict:
        """
        Method to convert model object into dict as required for server response for the api: POST./api/data-sources.
        :return:
        """
        return super().convert_model_to_dict()

    def _create_model_for_type(self, node_type: str, **kwargs):
        """
        Method to create model object for a specific node type

        :param node_type: node type defining the model object
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def _get_parent_node_type(self, child_node_type) -> str:
        """
        TODO: Consider eliminating this method's purpose by passing an arg inside _set_model(self, **kwargs)

        Method to get parent node type from child node type

        :param child_node_type: child node type
        :return:
        """
        raise NotImplementedError()
