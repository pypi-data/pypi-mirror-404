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

from hyrrokkin.interfaces.schema_api import PackageTypeApi, NodeTypeApi, LinkTypeApi
from hyrrokkin.utils.type_hints import JsonType
from .node_type import NodeType
from .link_type import LinkType


class PackageType(PackageTypeApi):

    def __init__(self, package_id, engine_package):
        self.package_id = package_id
        self.metadata = engine_package.get_metadata()
        self.node_types = {}
        self.link_types = {}
        for node_type_id, engine_node_type in engine_package.get_node_types().items():
            self.node_types[node_type_id] = NodeType(node_type_id, engine_node_type)

        for link_type_id, engine_link_type in engine_package.get_link_types().items():
            self.link_types[link_type_id] = LinkType(link_type_id, engine_link_type)

    def get_metadata(self) -> dict[str, JsonType]:
        return self.metadata

    def get_package_id(self) -> str:
        return self.package_id

    def get_node_types(self) -> dict[str, NodeTypeApi]:
        return self.node_types

    def get_link_types(self) -> dict[str, LinkTypeApi]:
        return self.link_types

    def __repr__(self):
        s = "Metadata:\n"
        for key, value in self.metadata.items():
            s += f"\t{key}: {value}\n"
        s = "Node Types:\n"
        for node_id, node_type in self.node_types.items():
            s += "\t" + node_id + ":\n"
            lines = str(node_type).split("\n")
            for line in lines:
                s += "\t\t" + line + "\n"
        s += "Link Types:\n"
        for link_id, link_type in self.link_types.items():
            s += "\t" + link_id + ":\n"
            lines = str(link_type).split("\n")
            for line in lines:
                s += "\t\t" + line + "\n"
        return s
