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

from .port_type import PortType

class NodeType:

    def __init__(self, metadata, input_ports, output_ports):
        self.metadata = metadata
        self.input_ports = input_ports
        self.output_ports = output_ports

    def get_metadata(self):
        return self.metadata

    def get_input_ports(self):
        return self.input_ports.items()

    def get_output_ports(self):
        return self.output_ports.items()

    def allow_multiple_input_connections(self, input_port_name):
        return self.input_ports[input_port_name].allows_multiple_connections()

    def allow_multiple_output_connections(self, output_port_name):
        return self.output_ports[output_port_name].allows_multiple_connections()

    def get_input_link_type(self, input_port_name):
        return self.input_ports[input_port_name].get_link_type()

    def get_output_link_type(self, output_port_name):
        return self.output_ports[output_port_name].get_link_type()

    @staticmethod
    def load(from_dict):
        return NodeType(metadata=from_dict.get("metadata", {}),
                        input_ports={name: PortType.load(port_dict, True) for (name, port_dict) in
                                     from_dict.get("input_ports", {}).items()},
                        output_ports={name: PortType.load(port_dict, False) for (name, port_dict) in
                                      from_dict.get("output_ports", {}).items()})
