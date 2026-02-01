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
import typing
from typing import Union, List, Dict

JsonType = Union[Dict[str, "JsonType"], List["JsonType"], str, int, float, bool, None]

class ConfigurationServiceInterface:

    @abstractmethod
    def resolve_resource(self, resource_path:str) -> str:
        """
        Resolve a relative resource path based on the location of the package schema

        Args:
            resource_path: the file path to resolve

        Returns:
            resolved path as a string containing a URL
        """

    @abstractmethod
    def get_package_version(self) -> str:
        """
        Get the package version string from the schema.json metadata

        Returns: package version string or "" if no version is defined in the metadata
        """

    @abstractmethod
    def set_status(self, status_message: str = "", level: typing.Literal["info", "warning", "error"] = "info"):
        """
        Set a status message for the package configuration.

        Args:
            status_message: a short descriptive message
            level: whether the message is "info", "warning" or "error"
        """

    @abstractmethod
    def clear_status(self):
        """
        Clear the status message for the package configuration.
        """
        pass

    @abstractmethod
    async def get_properties(self) -> dict[str,JsonType]:
        """
        Get the current properties associated with this configuration

        Returns:
            properties
        """
        pass

    @abstractmethod
    async def set_properties(self, properties:dict[str,JsonType]):
        """
        Set the current value for the configuration's property

        Args:
            properties: the properties to set

        Notes:
            properties should be a dictionary that is JSON-serialisable
        """
        pass


    @abstractmethod
    async def get_data(self, key: str) -> typing.Union[bytes, None]:
        """
        Get binary data associated with this package configuration.

        Args:
            key: a key to locate the data (can only contain alphanumeric characters and underscores)

        Returns:
            data or None if no data is associated with the key
        """
        pass

    @abstractmethod
    async def set_data(self, key: str, data: typing.Union[bytes, None]):
        """
        Set binary data associated with this package configuration.

        Args:
            key: a key to locate the data (can only contain alphanumeric characters and underscores)
            data: binary data (bytes) to be stored (or None to remove previously stored data for this key)
        """
        pass

    @abstractmethod
    async def get_data_keys(self) -> list[str]:
        """
        Returns the set of keys for which data is stored in this configuration

        Returns:
            list of key names
        """
        pass

    @abstractmethod
    def get_configuration(self, package_id:str) -> typing.Union[None,"hyrrokkin_engine.ConfigurationInterface"]:
        """
        Obtain a configuration object if defined for the specified package.

        Args:
            package_id: the id of the package configuration to obtain

        Returns:
            a configuration object or None
        """
        pass

    @abstractmethod
    def request_open_client(self, client_name: str, session_id: str):
        """
        Called to request that a client of this configuration be opened

        Args:
            client_name: the type of client to load
            session_id: specify which session to send the request to (defaults to all sessions)
        """
        pass

