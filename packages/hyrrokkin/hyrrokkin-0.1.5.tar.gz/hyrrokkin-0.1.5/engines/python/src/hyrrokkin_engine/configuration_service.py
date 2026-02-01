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

from .configuration_service_interface import ConfigurationServiceInterface, JsonType

class ConfigurationService(ConfigurationServiceInterface):

    def __init__(self, package_id, package_version, base_path):
        self.package_id = package_id
        self.package_version = package_version
        self.wrapper = None
        self.base_path = base_path

    def set_wrapper(self, wrapper):
        self.wrapper = wrapper

    def resolve_resource(self, resource_path: str):
        return os.path.join(self.base_path, resource_path)

    def get_package_version(self) -> str:
        return self.package_version

    def set_status(self, status_message:str="", level: typing.Literal["info","warning","error"]="info"):
        self.wrapper.set_status(level, status_message)

    def clear_status(self):
        self.wrapper.set_status("", "")

    async def get_properties(self) -> dict[str, JsonType]:
        return await self.wrapper.get_properties()

    async def set_properties(self, properties: dict[str, JsonType]):
        await self.wrapper.set_properties(properties)

    async def get_data(self, key: str) -> typing.Union[bytes, None]:
        return await self.wrapper.get_data(key)

    async def set_data(self, key: str, data: typing.Union[bytes, None]):
        await self.wrapper.set_data(key, data)

    async def get_data_keys(self):
        return await self.wrapper.get_data_keys()

    def get_configuration(self, package_id:str) -> typing.Union[None,ConfigurationServiceInterface]:
        wrapper = self.wrapper.get_configuration_wrapper(package_id)
        if wrapper is None:
            return None
        return wrapper.get_instance()

    def request_open_client(self, client_name: str, session_id:str = None):
        self.wrapper.request_open_client(client_name, session_id)
