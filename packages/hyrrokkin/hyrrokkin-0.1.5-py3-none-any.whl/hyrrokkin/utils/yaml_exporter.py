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

import os
from yaml import dump


def export_to_yaml(from_topology, to_path, include_data=True):
    node_ids = from_topology.get_node_ids()
    package_ids = from_topology.get_package_ids()
    to_folder = os.path.split(to_path)[0]
    with open(to_path, "w") as to_file:

        exported = {
            "metadata": from_topology.get_metadata(),
            "nodes": {},
            "links": []
        }

        configurations = {}

        for package_id in package_ids:
            package_properties = from_topology.get_configuration_properties(package_id)

            if len(package_properties) > 0:
                configurations[package_id] = {"properties": package_properties}
            if include_data:
                data_paths = {}
                data_keys = from_topology.get_configuration_data_keys(package_id)
                for data_key in data_keys:
                    data_folder = os.path.join(to_folder, "configuration", package_id, "data")
                    if not os.path.exists(data_folder):
                        os.makedirs(data_folder)
                    data_path = os.path.join(data_folder, data_key)
                    with open(data_path, "wb") as f:
                        f.write(from_topology.get_configuration_data(package_id, data_key))
                    data_paths[data_key] = os.path.relpath(data_path, to_folder)
                if len(data_keys):
                    if package_id not in configurations:
                        configurations[package_id] = {}
                    configurations[package_id]["data"] = data_paths

        if len(configurations):
            exported["configurations"] = configurations

        node_types = {}
        for node_id in node_ids:
            package_id, node_type = from_topology.get_node_type(node_id)
            properties = from_topology.get_node_properties(node_id)
            fq_node_type = package_id + ":" + node_type
            node_types[node_id] = fq_node_type
            exported["nodes"][node_id] = {"type": fq_node_type}
            if len(properties) > 0:
                exported["nodes"][node_id]["properties"] = properties
            if include_data:
                data_paths = {}
                data_keys = from_topology.get_node_data_keys(node_id)
                for data_key in data_keys:
                    data_folder = os.path.join(to_folder, "node", node_id, "data")
                    if not os.path.exists(data_folder):
                        os.makedirs(data_folder)
                    data_path = os.path.join(data_folder, data_key)
                    with open(data_path, "wb") as f:
                        f.write(from_topology.get_node_data(node_id, data_key))
                    data_paths[data_key] = os.path.relpath(data_path, to_folder)
                if len(data_keys) > 0:
                    exported["nodes"][node_id]["data"] = data_paths

        link_ids = from_topology.get_link_ids()
        for link_id in link_ids:
            from_node_id, from_port, to_node_id, to_port = from_topology.get_link(link_id)
            from_ports = from_topology.get_output_port_names(from_node_id)
            to_ports = from_topology.get_input_port_names(to_node_id)
            s = from_node_id
            if len(from_ports) > 1:
                s += ":" + from_port
            s += " => "
            s += to_node_id
            if len(to_ports) > 1:
                s += ":" + to_port
            exported["links"].append(s)

        dump(exported, to_file, default_flow_style=False, sort_keys=False)
