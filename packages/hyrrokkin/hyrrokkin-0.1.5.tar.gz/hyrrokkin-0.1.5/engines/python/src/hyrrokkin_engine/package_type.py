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

from .node_type import NodeType
from .link_type import LinkType

class PackageType:

    def __init__(self, id, metadata, node_types, link_types, configuration):
        self.id = id
        self.metadata = metadata
        self.node_types = node_types
        self.link_types = link_types
        self.configuration = configuration
        self.schema = None

    def get_node_types(self):
        return self.node_types

    def get_link_types(self):
        return self.link_types

    def get_id(self):
        return self.id

    def get_metadata(self):
        return self.metadata

    def get_node_type(self, node_type_id):
        return self.node_types[node_type_id]

    def get_configuration(self):
        return self.configuration

    def set_schema(self, schema):
        self.schema = schema

    def get_schema(self):
        return self.schema

    @staticmethod
    def load(from_dict):
        node_types = from_dict.get("node_types", {})
        node_types = {id: NodeType.load(node_type_dict) for (id, node_type_dict) in
                      node_types.items()}

        link_types = from_dict.get("link_types", {})
        if isinstance(link_types, list):
            link_types = {link_type["id"]: LinkType.load(link_type) for link_type in link_types}
        else:
            link_types = {id: LinkType.load(link_type_dict) for (id, link_type_dict) in link_types.items()}

        configuration = from_dict.get("configuration", {})

        p = PackageType(
            from_dict["id"],
            from_dict.get("metadata", {}),
            node_types,
            link_types,
            configuration
        )
        p.set_schema(from_dict)
        return p
