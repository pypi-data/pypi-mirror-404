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
import json
from importlib.resources import files

from hyrrokkin.utils.package_l10n import PackageL10N
from hyrrokkin_engine.package_type import PackageType


class Schema:
    supported_languages = ["py", "js"]

    def __init__(self):
        self.packages = {}
        self.package_l10n = {}
        self.package_paths = {}
        self.package_resources = {}

    def get_packages(self):
        return self.packages

    def get_package(self, package_id):
        return self.packages[package_id]

    def get_node_type(self, node_type_name):
        (package_id, node_type_id) = Schema.split_descriptor(node_type_name)
        return self.packages[package_id].get_node_type(node_type_id)

    @staticmethod
    def get_path_of_resource(package, resource=""):
        if resource:
            return str(files(package).joinpath(resource))
        else:
            return str(files(package))

    def load_package(self, resource):
        if "/" in resource:
            # resource is a file path
            schema_path = os.path.join(resource, "schema.json")
        else:
            # resource is a package?
            schema_path = Schema.get_path_of_resource(resource, "schema.json")
        with open(schema_path) as f:
            package_content = json.loads(f.read())
            package_path = os.path.split(schema_path)[0]
            package = PackageType.load(package_content)
            l10n = PackageL10N.load(package_content, package_path)
            self.add_package(package,l10n=l10n)
            self.package_paths[package.get_id()] = package_path
            self.package_resources[package.get_id()] = resource
            return package.get_id()

    def add_package(self, package, l10n=None):
        package_id = package.get_id()
        if package_id in self.packages:
            raise Exception("package %s already exists in schema" % (package_id))
        self.packages[package_id] = package
        if l10n is not None:
            self.package_l10n[package_id] = l10n

    def save(self):
        return [package.save() for package in self.packages.values()]

    def get_package_path(self, package_id):
        return self.package_paths[package_id]

    def get_package_resource(self, package_id):
        return self.package_resources[package_id]

    @staticmethod
    def split_descriptor(descriptor):
        comps = descriptor.split(":")
        if len(comps) > 2:
            raise Exception("Invalid descriptor: %s")
        if len(comps) == 2:
            return (comps[0], comps[1])
        else:
            return (None, comps[1])

    @staticmethod
    def form_descriptor(package_id, id):
        if not package_id:
            return id
        else:
            return "%s:%s" % (package_id, id)

    def get_localisation_bundle(self, package_id, for_language=""):
        if package_id in self.package_l10n:
            return self.package_l10n[package_id].get_bundle(for_language)
        return ("", {})

