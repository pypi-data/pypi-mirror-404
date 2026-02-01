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
import shutil
import logging
import json
import zipfile

from hyrrokkin.utils.hyrrokkin_utils import HyrrokkinUtils
from hyrrokkin.core.schema import Schema


class TopologyDirectory:

    def __init__(self, topology_folder, packages, applications={}, templates={}, topology_update_callback=None):
        """
        Create a TopologyDirectory instance for managing a set of topologies stored under a filesystem folder
        Args:
            topology_folder: the folder under which each topology in the directory is stored, with the directory name as the topology id
            packages: a list of the paths to python packages containing hyrrokkin package schemas (a schema.json file)
            applications: a dictionary mapping from application_id to a dictionary describing the application (FIXME more details needed)
            templates: a dictionary mapping from topology_id to a dictionary describing the template for that topology id (FIXME more details needed)
            topology_update_callback: a callback that is called with 2 arguments (action,topology_id) where action is "create", "remove" or "reload"
        """
        self.workspace_folder = topology_folder
        self.packages = packages

        self.templates = templates
        self.topology_update_callback = topology_update_callback

        self.schema = Schema()
        for package in packages:
            self.schema.load_package(package)
        self.logger = logging.getLogger("TopologyDirectory")

        for topology_id in self.templates:
            # for each template...
            topology_folder = os.path.join(self.workspace_folder, topology_id)
            if not os.path.exists(topology_folder):
                # if no topology already exists, unpack the template
                package = self.templates[topology_id]["package"]
                resource = self.templates[topology_id]["resource"]
                self.logger.info(f"loading {topology_id} from template {package} {resource}")
                TopologyDirectory.load_template(package, resource, topology_folder)

        self.applications = {}
        self.application_paths = {}
        for application_id, application in applications.items():
            path = HyrrokkinUtils.get_path_of_resource(application["package"], application["resource"])
            with open(path) as f:
                application_definition = json.loads(f.read())

            label = application.get("label", application_definition.get("metadata", {}).get("name", application_id))
            self.applications[application_id] = {
                "label": label
            }
            if "application_url" in application:
                self.applications[application_id]["application_url"] = application["application_url"]
            self.application_paths[application_id] = path

    def get_package_path(self, package_id):
        return self.schema.get_package_path(package_id)

    def get_application_path(self, application_id):
        return self.application_paths[application_id]

    def get_topology_folder(self, topology_id):
        return os.path.join(self.workspace_folder, topology_id)

    def create_topology(self, topology_id, from_topology_id=None):
        """
        Create a topology in this directory
        Args:
            topology_id: the id of the topology to create
            from_topology_id: optional, the id of an existing topology to copy

        Returns:
            dictionary containing metadata from the newly created topology
        """
        to_folder = self.get_topology_folder(topology_id)

        if from_topology_id:
            from_folder = self.get_topology_folder(from_topology_id)
            if os.path.isdir(from_folder):
                shutil.copytree(from_folder, to_folder)
            elif from_topology_id in self.templates:
                TopologyDirectory.load_template(self.templates[from_topology_id]["path"], to_folder)
            else:
                self.logger.warning(
                    f"Unable to create {topology_id} from {from_topology_id}, creating an empty topology instead...")

        # create an empty topology if necessary
        path = os.path.join(to_folder, "topology.json")
        if not os.path.exists(path):
            folder = os.path.dirname(path)
            os.makedirs(folder, exist_ok=True)
            with open(path, "w") as f:
                f.write(json.dumps({"nodes": {}, "links": {}, "metadata": {}}, indent=4))
        with open(path, "r") as f:
            topology = json.loads(f.read())
        if self.topology_update_callback:
            self.topology_update_callback("create", topology_id)
        return topology["metadata"]

    def remove_topology(self, topology_id):
        """
        Remove a topology from this directory, removing all files related to the topology.

        Args:
            topology_id: the id of the topology to remove
        """
        topology_folder = self.get_topology_folder(topology_id)
        if os.path.exists(topology_folder):
            shutil.rmtree(topology_folder)
        if self.topology_update_callback:
            self.topology_update_callback("remove", topology_id)

    def reload_topology(self, topology_id):
        """
        Reload a topology in this directory from a template for that topology_id (if exists) or re-create an empty topology

        Args:
            topology_id: the id of the topology to reload
        """
        self.remove_topology(topology_id)
        if topology_id in self.templates:
            topology_folder = self.get_topology_folder(topology_id)
            TopologyDirectory.load_template(self.templates[topology_id]["package"], self.templates[topology_id]["resource"], topology_folder)
        else:
            # no template to reload
            self.logger.warning(
                f"Unable to reload {topology_id}, no template exists.  Creating an empty topology instead...")
            self.create_topology(topology_id)
        if self.topology_update_callback:
            self.topology_update_callback("reload", topology_id)

    @staticmethod
    def load_template(package, resource, topology_folder):
        os.makedirs(topology_folder)
        zip_path = HyrrokkinUtils.get_path_of_resource(package, resource)
        zf = zipfile.ZipFile(zip_path, mode="r")
        zf.extractall(topology_folder)

    def get_packages(self):
        return self.packages

    def get_package_ids(self):
        return list(self.schema.get_packages().keys())

    def get_topologies(self):
        return HyrrokkinUtils.list_topologies(self.workspace_folder)

    def get_applications(self):
        return self.applications

    def get_templates(self):
        return self.templates


