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

from hyrrokkin.interfaces.schema_api import NodeTypeApi, PortTypeApi
from .port_type import PortType
from hyrrokkin.utils.type_hints import JsonType


class NodeType(NodeTypeApi):

    def __init__(self, node_type_id, engine_node_type):
        self.node_type_id = node_type_id
        self.metadata = engine_node_type.get_metadata()
        self.input_port_types = {}
        self.output_port_types = {}
        for input_port_name, input_port in engine_node_type.get_input_ports():
            self.input_port_types[input_port_name] = PortType(input_port)
        for output_port_name, output_port in engine_node_type.get_output_ports():
            self.output_port_types[output_port_name] = PortType(output_port)

    def get_node_type_id(self) -> str:
        return self.node_type_id

    def get_metadata(self) -> dict[str, JsonType]:
        return self.metadata

    def get_input_ports(self) -> dict[str, PortTypeApi]:
        return self.input_port_types

    def get_output_ports(self) -> dict[str, PortTypeApi]:
        return self.output_port_types

    def __repr__(self):
        s = "Metadata:\n"
        for key, value in self.metadata.items():
            s += f"\t{key}: {value}\n"
        s += "Input Ports:\n"
        for input_port_name, port_type in self.input_port_types.items():
            s += "\t" + input_port_name + ":\n"
            lines = str(port_type).split("\n")
            for line in lines:
                s += "\t\t" + line + "\n"
        s += "Output Ports:\n"
        for output_port_name, port_type in self.output_port_types.items():
            s += "\t" + output_port_name + ":\n"
            lines = str(port_type).split("\n")
            for line in lines:
                s += "\t\t" + line + "\n"
        return s
