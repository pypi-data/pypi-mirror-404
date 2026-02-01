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

import typing
import os.path

from typing import Union, Dict, List, Literal

from .node_service_interface import NodeServiceInterface
from .configuration_interface import ConfigurationInterface

JsonType = Union[Dict[str, "JsonType"], List["JsonType"], str, int, float, bool, None]

class NodeService(NodeServiceInterface):

    """
    Defines a set of services that a Hyrrokkin node can access.
    """
    def __init__(self, node_id: str, base_path:str):
        self.node_id = node_id
        self.base_path = base_path
        self.wrapper = None
        self.active = True

    def set_wrapper(self, wrapper):
        self.wrapper = wrapper

    def resolve_resource(self, resource_path: str):
        return os.path.join(self.base_path, resource_path)

    def get_node_id(self) -> str:
        return self.node_id

    def set_status(self, status_message:str="", level:Literal["info","warning","error"]="info"):
        if self.active:
            self.wrapper.set_status(level, status_message)

    def clear_status(self):
        if self.active:
            self.wrapper.set_status("", "")

    def set_running_state(self, state:str):
        if self.active:
            self.wrapper.set_running_state(state)

    async def request_run(self):
        if self.active:
            await self.wrapper.request_run()

    async def get_properties(self) -> dict[str,JsonType]:
        if self.active:
            return await self.wrapper.get_properties()

    async def set_properties(self, properties:dict[str,JsonType]):
        if self.active:
            return await self.wrapper.set_properties(properties)

    async def get_data(self, key:str) -> typing.Union[bytes,None]:
        if self.active:
            return await self.wrapper.get_data(key)

    async def set_data(self, key:str, data:typing.Union[bytes,None]):
        if self.active:
            await self.wrapper.set_data(key, data)

    async def get_data_keys(self):
        if self.active:
            return await self.wrapper.get_data_keys()

    def get_configuration(self, package_id:str=None) -> typing.Union[None,ConfigurationInterface]:
        if self.active:
            return self.wrapper.get_configuration_wrapper(package_id).get_instance()

    def request_open_client(self, client_name: str, session_id:str = None):
        if self.active:
            self.wrapper.request_open_client(client_name, session_id)

    def get_connection_count(self, port_name:str, port_direction:str) -> int:
        if self.active:
            return self.wrapper.get_connection_count(port_name, port_direction)

    def deactivate(self):
        self.active = False







    




