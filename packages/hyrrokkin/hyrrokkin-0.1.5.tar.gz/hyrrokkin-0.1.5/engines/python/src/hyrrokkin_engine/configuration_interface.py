#   Hyrrokkin - a library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this software
#   and associated documentation files (the "Software"), to deal in the Software without
#   restriction, including without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or
#   substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#   BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from abc import abstractmethod
from typing import Any

from .configuration_service import ConfigurationService
from .node_service_interface import NodeServiceInterface
from .client_interface import ClientInterface

class ConfigurationInterface:

    @abstractmethod
    def __init__(self, services:ConfigurationService):
        """
        Create an instance of this Configuration

        Args:
            services: an object providing useful services, for example to get or set property values
        """
        pass

    @abstractmethod
    async def load(self):
        """
        Called after construction.  Load any resources associated with this Configuration
        """
        pass

    @abstractmethod
    async def create_node(self, node_type_id:str, service:NodeServiceInterface):
        """
        Create a node which is defined within this package

        :param node_type_id: the id of the node type (a valid key in the schema's node_types dictionary)
        :param service: a service instance which will provide services to the node

        :return: an instance of the node
        """
        pass

    @abstractmethod
    async def decode(self, encoded_bytes:bytes, link_type:str) -> Any:
        """
        Decode binary data into a value valid for a particular link type

        :param encoded_bytes: binary data to decode
        :param link_type: the link type associated with the value
        :return: decoded value
        """
        pass

    @abstractmethod
    async def encode(self, value:Any, link_type: str) -> bytes:
        """
        Encode a value associated with a link type to binary data

        :param value: the value to encode
        :param link_type: the link type associated with the value
        :return: binary data that encodes the value
        """
        pass

    @abstractmethod
    def open_session(self, session_id):
        """
        Called when a new session starts
        """
        pass

    @abstractmethod
    def close_session(self, session_id):
        """
        Called when a session closes
        """
        pass

    @abstractmethod
    async def open_client(self, client:ClientInterface):
        """
        Called when a client is attached to the configuration

        Arguments:
            client: a service instance allowing messages to be sent to and received from the client
        """
        pass

    @abstractmethod
    async def close_client(self, client:ClientInterface):
        """
        Called when a client is detached from the configuration

        Arguments:
            client: a service instance allowing messages to be sent to and received from the client
        """
        pass



    