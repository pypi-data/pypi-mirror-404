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

import os.path
import os
import json
import importlib

class Serde:

    def __init__(self, schema):
        self.schema = schema
        self.package_configuration_classes = {}
        for package_id in schema.get_packages():
            package_path = schema.get_package_path(package_id)
            python_json_path = os.path.join(package_path, 'python.json')
            if os.path.exists(python_json_path):
                with open(python_json_path, 'r') as f:
                    o = json.loads(f.read())
                    configuration_class_path = o["configuration_class"]
                    if configuration_class_path.startswith("."):
                        configuration_class_path = schema.get_package_resource(package_id) + configuration_class_path
                    configuration_module = importlib.import_module(".".join(configuration_class_path.split(".")[:-1]))
                    configuration_class = getattr(configuration_module, configuration_class_path.split(".")[-1])
                    self.package_configuration_classes[package_id] = configuration_class

    def serialise(self, value, package_id, node_type_id, input_port_name):
        package_type = self.schema.get_package(package_id)
        node_type = package_type.get_node_type(node_type_id)
        link_type = node_type.get_input_link_type(input_port_name)
        if ":" in link_type:
            link_package_id = link_type.split(":")[0]
            link_type = link_type.split(":")[1]
        else:
            link_package_id = package_id
        configuration_class = self.package_configuration_classes[link_package_id]
        return configuration_class.encode(value, link_type)

    def deserialise(self, value, package_id, node_type_id, output_port_name):
        package_type = self.schema.get_package(package_id)
        node_type = package_type.get_node_type(node_type_id)
        link_type = node_type.get_output_link_type(output_port_name)
        if ":" in link_type:
            link_package_id = link_type.split(":")[0]
            link_type = link_type.split(":")[1]
        else:
            link_package_id = package_id
        configuration_class = self.package_configuration_classes[link_package_id]
        return configuration_class.decode(value, link_type)
