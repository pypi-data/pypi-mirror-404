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
import json
from typing import Literal

from .engine_launcher import EngineLauncher


class JavascriptEngineLauncher(EngineLauncher):

    def __init__(self, persistence: Literal["memory", "filesystem"] = "memory", verbose=False):
        super().__init__(persistence=persistence, verbose=verbose)
        self.source_paths = []

    def get_name(self):
        return f"Javascript-Engine[Deno,persistence={self.persistence}]"

    COMMON_JS = [
        "hyrrokkin_engine/client_interface.js",
        "hyrrokkin_engine/client.js",
        "hyrrokkin_engine/message_utils.js",
        "hyrrokkin_engine/wrapper.js",
        "hyrrokkin_engine/port_type.js",
        "hyrrokkin_engine/link_type.js",
        "hyrrokkin_engine/node_type.js",
        "hyrrokkin_engine/package_type.js",
        "hyrrokkin_engine/configuration_service_interface.js",
        "hyrrokkin_engine/configuration_service.js",
        "hyrrokkin_engine/configuration_wrapper.js",
        "hyrrokkin_engine/node_service_interface.js",
        "hyrrokkin_engine/node_service.js",
        "hyrrokkin_engine/node_wrapper.js",
        "hyrrokkin_engine/graph_link.js",
        "hyrrokkin_engine/graph_executor.js",
        "hyrrokkin_engine/node_interface.js",
        "hyrrokkin_engine/configuration_interface.js",
        "hyrrokkin_engine/persistence_interface.js",
        "hyrrokkin_engine_drivers/common/persistence.js",
        "hyrrokkin_engine_drivers/common/persistence_memory.js",
        "hyrrokkin_engine_drivers/deno/persistence_deno_filesystem.js",
        "hyrrokkin_engine_drivers/execution_worker.js",
        "hyrrokkin_engine/registry.js",
        "hyrrokkin_engine_utils/expression_checker.js",
        "hyrrokkin_engine_utils/expression_parser.js",
        "hyrrokkin_engine_utils/value_iterable.js",
        "hyrrokkin_engine_utils/value_stream.js",
        "hyrrokkin_engine_utils/value_collection.js"
    ]

    DENO_JS = [
        "hyrrokkin_engine_drivers/deno/persistence_deno_filesystem.js",
        "hyrrokkin_engine_drivers/deno/engine_driver.js"
    ]

    def get_commandline(self, host_name, port):
        return ["deno", "--allow-net", "--allow-read", "--allow-write", "-", str(host_name), str(port),
                "verbose" if self.verbose else "quiet"]

    def get_worker_configuration(self):
        return {}

    def configure_package(self, package_id, package_resource, package_folder):
        config_path = os.path.join(package_folder, self.get_configuration_filename())
        with open(config_path) as f:
            o = json.loads(f.read())
            for source_path in o["source_paths"]:
                self.source_paths.append(os.path.join(package_folder, source_path))

    def get_inputs(self):
        folder = os.path.split(__file__)[0]
        engine_paths = []
        for path in JavascriptEngineLauncher.COMMON_JS:
            engine_paths.append(os.path.join(folder, "..", "..", "..", "engines", "javascript", "src", path))
        deno_engine_paths = []
        for path in JavascriptEngineLauncher.DENO_JS:
            deno_engine_paths.append(os.path.join(folder, "..", "..", "..", "engines", "javascript", "src", path))

        for fname in engine_paths + self.source_paths + deno_engine_paths:
            with open(fname) as f:
                yield f.read()

    def get_configuration_filename(self):
        return "javascript.json"
