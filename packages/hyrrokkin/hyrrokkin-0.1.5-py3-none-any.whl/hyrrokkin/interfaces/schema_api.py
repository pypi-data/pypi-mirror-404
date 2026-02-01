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

from hyrrokkin.utils.type_hints import JsonType, MessageHandler
from abc import abstractmethod, ABC


class PortTypeApi(ABC):

    @abstractmethod
    def get_metadata(self) -> dict[str, JsonType]:
        """
        Returns: a json-serialisable dictionary contining the port's metadata
        """

    @abstractmethod
    def get_link_type(self) -> str:
        """

        Returns:

        """

    def get_allow_multiple_connections(self) -> bool:
        """
        Returns:
        """

    @abstractmethod
    def __repr__(self) -> str:
        """
        Returns:
             a string representation of the port type
        """


class NodeTypeApi(ABC):

    @abstractmethod
    def get_node_type_id(self) -> str:
        """

        Returns:

        """

    @abstractmethod
    def get_metadata(self) -> dict[str, JsonType]:
        """

        Returns:

        """

    def get_input_ports(self) -> dict[str, PortTypeApi]:
        """

        Returns:

        """

    def get_output_ports(self) -> dict[str, PortTypeApi]:
        """

        Returns:

        """

    @abstractmethod
    def __repr__(self) -> str:
        """
        Returns:
             a string representation of the node type
        """


class LinkTypeApi(ABC):

    @abstractmethod
    def get_link_type_id(self) -> str:
        """

        Returns:

        """

    @abstractmethod
    def get_metadata(self) -> dict[str, JsonType]:
        """

        Returns:

        """

    @abstractmethod
    def __repr__(self) -> str:
        """
        Returns:
             a string representation of the link type
        """


class PackageTypeApi(ABC):

    @abstractmethod
    def get_metadata(self) -> dict[str, JsonType]:
        """

        Returns:

        """

    @abstractmethod
    def get_package_id(self) -> str:
        """

        Returns:

        """

    @abstractmethod
    def get_node_types(self) -> dict[str, NodeTypeApi]:
        """

        Returns:

        """

    @abstractmethod
    def get_link_types(self) -> dict[str, LinkTypeApi]:
        """

        Returns:

        """

    @abstractmethod
    def __repr__(self) -> str:
        """
        Returns:
             a string representation of the package
        """


class SchemaTypeApi(ABC):

    @abstractmethod
    def get_packages(self) -> dict[str, PackageTypeApi]:
        """

        Returns:

        """

    @abstractmethod
    def __repr__(self) -> str:
        """
        Returns:
             a string representation of the schema
        """
