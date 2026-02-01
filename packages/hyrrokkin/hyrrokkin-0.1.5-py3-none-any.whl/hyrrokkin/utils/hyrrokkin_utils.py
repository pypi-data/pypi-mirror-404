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

import logging
import os
import json
from importlib.resources import files


class HyrrokkinUtils:
    logger = logging.getLogger("HyrrokkinUtils")

    @staticmethod
    def get_path_of_resource(package, resource=""):
        if resource:
            return str(files(package).joinpath(resource))
        else:
            return str(files(package))

    @staticmethod
    def list_topologies(workspace_folder):
        topologies = {}
        os.makedirs(workspace_folder, exist_ok=True)
        if os.path.isdir(workspace_folder):
            topology_ids = os.listdir(workspace_folder)
            for topology_id in topology_ids:
                topology_path = os.path.join(workspace_folder, topology_id, "topology.json")
                try:
                    package_ids = []
                    with open(topology_path) as f:
                        obj = json.loads(f.read())
                        metadata = obj.get("metadata", {})
                        for node_id in obj.get("nodes", {}):
                            node_type = obj["nodes"][node_id].get("node_type", "")
                            if node_type:
                                package_id = node_type.split(":")[0]
                                if package_id not in package_ids:
                                    package_ids.append(package_id)

                    topologies[topology_id] = {"metadata": metadata, "package_ids": package_ids}
                except Exception as ex:
                    HyrrokkinUtils.logger.exception(f"reading topology {topology_id}")
        return topologies
