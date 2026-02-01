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

from hyrrokkin.interfaces.schema_api import PortTypeApi
from hyrrokkin.utils.type_hints import JsonType


class PortType(PortTypeApi):

    def __init__(self, engine_port):
        self.metadata = engine_port.get_metadata()
        self.link_type = engine_port.get_link_type()
        self.allow_multiple_connections = engine_port.allows_multiple_connections()

    def get_metadata(self) -> dict[str, JsonType]:
        return self.metadata

    def get_link_type(self) -> str:
        return self.link_type

    def get_allow_multiple_connections(self) -> bool:
        return self.allow_multiple_connections

    def __repr__(self):
        s = "Metadata:\n"
        for key, value in self.metadata.items():
            s += f"\t{key}: {value}\n"
        s += f"Allow Multiple Connections: {self.allow_multiple_connections}\n"
        s += f"Link Type: {self.link_type}\n"
        return s
