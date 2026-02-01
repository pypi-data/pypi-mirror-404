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
import sys
import importlib.metadata
import fnmatch
import logging
import tomllib

from hyrrokkin.execution_manager.process_runner import ProcessRunner
from hyrrokkin.api.topology import Topology
from hyrrokkin.service.topology_endpoint import TopologyEndpoint
from hyrrokkin.engine_launchers.python_engine_launcher import PythonEngineLauncher


def main():
    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("--topology-path", help="path of folder storing topology", default="topology")
    parser.add_argument("--options-path", metavar="PATH", type=str, help="path to TOML configuration file")
    parser.add_argument("--generate-example-options", type=str, metavar="PATH",
                        help="Generate a sample options file to this path and then exit", default=None)
    parser.add_argument("--launch-ui", type=str,
                        help="Desktop mode: specify a command launch a web browser on startup, for example \"chromium --app=URL\".  URL will be substituted for the url of the first workspace's directory. ",
                        default="")

    parser.add_argument("--base-path", help="base path of the URL to listen at", default="")
    parser.add_argument("--host", metavar="HOST", type=str, help="the host to bind to", default="localhost")
    parser.add_argument("--port", metavar="PORT", type=int, help="the port to bind to", default=9002)
    parser.add_argument("--import-path", help="topology file to import (.zip or .yaml/.yml)")
    parser.add_argument("--engine", choices=["javascript", "python", "auto"], default="python",
                        help="specify engine to run topology")
    parser.add_argument("--verbose", action="store_true", help="enable verbose logging")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = logging.getLogger("hyrrokkin-designer")

    if args.generate_example_options:
        with open(os.path.join(os.path.split(__file__)[0], "options.toml")) as f:
            contents = f.read()
            with open(args.generate_example_options) as of:
                of.write(contents)
        sys.exit(0)

    if args.options_path:
        options_path = args.options_path
    else:
        options_path = os.path.join(os.path.split(__file__)[0], "options.toml")

    with open(options_path) as f:
        options = tomllib.loads(f.read())

    package_list = []
    for include_package in options.get("include_packages", []):
        if include_package not in package_list:
            package_list.append(include_package)

    # add in all packages installed with the hyrrokkin_packages entrypoint...
    eps = importlib.metadata.entry_points()
    package_entrypoints = eps.select(group="hyrrokkin_packages")
    for entrypoint in package_entrypoints:
        if entrypoint.value not in package_list:
            package_list.append(entrypoint.value)

    # now remove any packages that were explicitly excluded...
    for excluded_package_pattern in options.get("exclude_packages", []):
        packages = package_list[:]
        for package in packages:
            if fnmatch.fnmatch(package, excluded_package_pattern):
                package_list.remove(package)

    if len(package_list) == 0:
        logger.warning("No packages loaded, adding example package hyrrokkin.example_packages.textgraph")
        package_list.append("hyrrokkin.example_packages.textgraph")

    launcher = PythonEngineLauncher(verbose=args.verbose)

    t = Topology(topology_folder=args.topology_path, package_list=package_list,
                 import_from_path=args.import_path, engine_launcher=launcher)

    local_url = f"http://{args.host}:{args.port}{args.base_path}/topology-designer.html"

    # called when the web server is listening
    def open_callback(server):
        if server.check_running():
            if args.launch_ui:
                # open a web browser on the directory of the first workspace
                cmd = args.launch_ui.replace("URL", local_url)
                pr = ProcessRunner(cmd.split(" "), exit_callback=lambda: server.stop())
                pr.start()

    s = TopologyEndpoint(args.host, args.port, base_path=args.base_path, topology=t, start_callback=open_callback)
    print(local_url)
    s.start()


if __name__ == '__main__':
    main()
