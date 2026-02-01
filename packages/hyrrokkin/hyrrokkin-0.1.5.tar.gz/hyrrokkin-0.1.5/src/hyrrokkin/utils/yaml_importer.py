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

from yaml import load, FullLoader
import os


def import_from_yaml(into_topology, from_path, include_data=True, include_configuration=True, include_metadata=True):
    from_folder = os.path.split(from_path)[0]

    added_node_ids = set()
    added_link_ids = set()
    node_renamings = {}
    with open(from_path, "r") as from_file:
        cfg = load(from_file, Loader=FullLoader)

        metadata = cfg.get("metadata", {})
        if include_metadata:
            into_topology.set_metadata(metadata)

        spec = cfg.get("configurations", {})
        if include_configuration:
            for package_id in spec:
                into_topology.set_configuration_properties(package_id, spec[package_id].get("properties", {}))
                configuration_data = spec.get("data", {})
                if include_data:
                    for key in configuration_data:
                        with open(os.path.join(from_folder, configuration_data[key]), "rb") as f:
                            into_topology.set_configuration_data(package_id, key, f.read())

        nodes = cfg.get("nodes", {})
        node_types = {}
        if nodes:
            for node_id in nodes:
                node_spec = nodes[node_id]
                node_type = node_spec["type"]
                node_metadata = node_spec.get("metadata", {})
                node_properties = node_spec.get("properties", {})
                added_node_id = into_topology.add_node(node_id, node_type, metadata=node_metadata,
                                                       properties=node_properties)
                added_node_ids.add(added_node_id)
                if added_node_id != node_id:
                    node_renamings[node_id] = added_node_id
                node_data = node_spec.get("data", {})
                if include_data:
                    for key in node_data:
                        with open(os.path.join(from_folder, node_data[key]), "rb") as f:
                            into_topology.set_node_data(added_node_id, key, f.read())
                node_types[node_id] = node_type

        links = cfg.get("links", [])
        if links:
            for idx in range(len(links)):
                link_id = "link" + str(idx)
                link_spec = cfg["links"][idx]
                from_to = link_spec.split("=>")
                from_parts = from_to[0].strip().split(":")
                from_node_id = from_parts[0]
                from_port = from_parts[1] if len(from_parts) > 1 else None
                to_parts = from_to[1].strip().split(":")
                to_node_id = to_parts[0]
                to_port = to_parts[1] if len(to_parts) > 1 else None

                added_link_id = into_topology.add_link(link_id, from_node_id, from_port, to_node_id, to_port)
                added_link_ids.add(added_link_id)

    return list(added_node_ids), list(added_link_ids), node_renamings
