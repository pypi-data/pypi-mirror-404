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
from typing import Dict, List, Any


from .node_service_interface import NodeServiceInterface
from .client_interface import ClientInterface

class NodeInterface:

    @abstractmethod
    def __init__(self, services: NodeServiceInterface):
        """
        Create an instance of this Node

        Args:
            services: an object providing useful services, for example to get or set property values
        """
        pass


    @abstractmethod
    async def load(self):
        """
        Called after construction.  Load any resources associated with this Node
        """
        pass

    @abstractmethod
    async def reset_run(self):
        """
        Called when this instance's node is about to be re-run
        """
        pass

    @abstractmethod
    async def open_client(self, client:ClientInterface):
        """
        Called when a client is attached to the node

        Arguments:
            client: a service instance allowing messages to be sent to and recieved from the client
        """
        pass

    @abstractmethod
    async def close_client(self, client:ClientInterface):
        """
        Called when a client is detached from the node

        Arguments:
            client: a service instance allowing messages to be sent to and recieved from the client

        Notes:
            a call to close_client is preceeded by a call to open_client with the same parameter
        """
        pass

    @abstractmethod
    async def run(self, inputs: Dict[str,List[Any]]) -> Dict[str,Any]:
        """
        Called when a node should transform input values into output values
        
        Arguments:
            inputs: a dictionary mapping input port names to a list of values being presented at that import port
        
        Returns:
            a dictionary mapping output port names to a value output on that port
        """
        pass

    @abstractmethod
    async def remove(self):
        """
        Called before the node instance is deleted
        """
        pass
