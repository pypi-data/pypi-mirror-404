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


import sys
import os
import json
from typing import Literal

from .engine_launcher import EngineLauncher


class PythonEngineLauncher(EngineLauncher):

    def __init__(self, persistence: Literal["memory", "filesystem"] = "memory",
                 verbose: bool = False):
        super().__init__(persistence=persistence, verbose=verbose)
        self.worker_configuration = {"packages": {}}

    def get_name(self):
        return f"Python-Engine[persistence={self.persistence}]"

    def get_commandline(self, host_name, port):
        cmdline = [sys.executable, "-m", "hyrrokkin_engine_drivers.execution_worker", str(host_name), str(port)]
        if self.verbose:
            cmdline.append("--verbose")
        return cmdline

    def configure_package(self, package_id, package_resource, package_folder):
        config_path = os.path.join(package_folder, self.get_configuration_filename())
        with open(config_path) as f:
            o = json.loads(f.read())
            configuration_class = o["configuration_class"]
            if configuration_class.startswith("."):
                configuration_class = package_resource + configuration_class
            self.worker_configuration["packages"][package_id] = {"configuration_class": configuration_class}

    def get_worker_configuration(self):
        return self.worker_configuration

    def get_configuration_filename(self):
        return "python.json"

