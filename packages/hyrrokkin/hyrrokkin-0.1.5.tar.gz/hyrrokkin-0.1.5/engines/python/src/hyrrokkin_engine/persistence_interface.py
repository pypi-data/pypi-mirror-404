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

from abc import abstractmethod
from typing import Union, Dict, List, Literal

JsonType = Union[Dict[str, "JsonType"], List["JsonType"], str, int, float, bool, None]


class PersistenceInterface:

    @abstractmethod
    async def get_properties(self):
        """
        Get the current properties associated with this node/configuration

        Returns:
            properties
        """
        pass

    @abstractmethod
    async def set_properties(self, properties):
        """
        Set the current value for the node/configuration's property

        Args:
            properties: the properties to set

        Notes:
            properties should be a dictionary that is JSON-serialisable
        """
        pass

    @abstractmethod
    async def get_data(self, key: str) -> typing.Union[bytes, None]:
        """
        Get binary data (bytes) associated with this node/configuration.

        Args:
            key: a key to locate the data (can only contain alphanumeric characters and underscores)

        Returns:
            data or None if no data is associated with the key
        """
        pass

    @abstractmethod
    async def set_data(self, key: str, data: typing.Union[bytes, None]):
        """
        Set binary data (bytes) associated with this node/configuration.

        Args:
            key: a key to locate the data (can only contain alphanumeric characters and underscores)
            data: binary data (bytes) to be stored (or None to remove previously stored data for this key)
        """
        pass

    @abstractmethod
    async def get_data_keys(self) -> list[str]:
        """
        Returns the set of keys for which data is stored in this node/configuration

        Returns:
            list of key names
        """
        pass




