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
import logging
import sys

from hyrrokkin.core.topology import Topology
from hyrrokkin.engine_launchers.javascript_engine_launcher import JavascriptEngineLauncher
from hyrrokkin.engine_launchers.python_engine_launcher import PythonEngineLauncher

banner = """
 _                               _     _     _
| |__   _   _  _ __  _ __  ___  | | __| | __(_) _ __
| '_ \\ | | | || '__|| '__|/ _ \\ | |/ /| |/ /| || '_ \\
| | | || |_| || |   | |  | (_) ||   < |   < | || | | |
|_| |_| \\__, ||_|   |_|   \\___/ |_|\\_\\|_|\\_\\|_||_| |_|
        |___/
"""


def main():
    import argparse

    print(banner)

    parser = argparse.ArgumentParser()

    parser.add_argument("--packages", nargs="+",
                        help="Specify hyrrokkin package(s) to be loaded (using dotted notation, eg hyrrokkin_example_packages.numbergraph)",
                        required=True)
    parser.add_argument("--execution-folder",
                        help="Folder to store and persist, required unless specifying --read-only", default="")
    parser.add_argument("--import-path", help="topology file to import (.zip or .yaml/.yml)")
    parser.add_argument("--export-path", help="topology file to export (.zip or .yaml/.yml)")
    parser.add_argument("--export-data", type=bool, help="include data when exporting to .zip or .yaml", default=True)
    parser.add_argument("--run", action="store_true", help="run the topology")

    parser.add_argument("--inject-input", action="append", nargs=3, metavar=("NODE", "PORT", "PATH"),
                        help="inject inputs")
    parser.add_argument("--output-listener", action="append", nargs=3, metavar=("NODE", "PORT", "PATH"),
                        help="collect outputs")
    parser.add_argument("--engine", choices=["javascript", "python", "auto"], default="auto",
                        help="specify engine to run topology")
    parser.add_argument("--read-only", action="store_true",
                        help="if running, do not persist any changes to properties/data, required if no execution folder is provided")
    parser.add_argument("--verbose", action="store_true", help="enable verbose logging")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = logging.getLogger("hyrrokkin-cli")

    t = Topology(execution_folder=args.execution_folder, package_list=args.packages)

    if args.import_path:
        suffix = os.path.splitext(args.import_path)[1]
        try:
            if suffix == ".zip":
                with open(args.import_path, "rb") as f:
                    t.load_zip(f)
            elif suffix == ".yaml" or suffix == ".yml":
                from hyrrokkin.utils.yaml_importer import import_from_yaml
                import_from_yaml(t, args.import_path)
            else:
                raise Exception("Unsupported input file type, expecting .zip, .yaml or .yml")
            logger.info(f"Imported topology from {args.import_path}")

        except Exception as ex:
            logger.exception(f"Error importing topology from {args.import_path}")
            sys.exit(0)

    if args.run:
        # work out which engine to use
        engine_launcher = None
        engine = args.engine
        if engine == "auto":
            pass
        elif engine == "javascript":
            engine_launcher = JavascriptEngineLauncher()
        elif engine == "python":
            engine_launcher = PythonEngineLauncher()

        logger.info(f"Using engine {str(engine_launcher)}")

        def status_handler(source_id, source_type, msg, status):
            if status == "info":
                logger.info(f"[{source_type}:{source_id}] - status - {msg}")
            elif status == "warning":
                logger.warning(f"[{source_type}:{source_id}] - status - {msg}")
            elif status == "error":
                logger.error(f"[{source_type}:{source_id}] - status - {msg}")
            elif status == "":
                # clear status, log nothing
                pass

        def excecution_handler(at_time, node_id, state, exception_or_result, is_manual):
            if state == "error":
                logger.exception(f"[node:{node_id}] execution error", exc_info=exception_or_result)
            else:
                logger.info(f"[node:{node_id}] execution state set to {state}")

        runner = t.open_runner(status_event_handler=status_handler, engine_launcher=engine_launcher,
                               execution_event_handler=excecution_handler, read_only=args.read_only)

        if args.inject_input:
            for (node_id, port, path) in args.inject_input:
                with open(path, "rb") as f:
                    runner.inject_input_value(node_id, port, f.read())

        if args.output_listener:
            def create_writer(node_id, port_name, path):
                def writer(value):
                    logger.info(f"[node:{node_id}] writing output from port {port_name} to {path}")
                    with open(path, "wb") as f:
                        f.write(value)

                return writer

            for (node_id, port, path) in args.output_listener:
                runner.add_output_listener(node_id, port, create_writer(node_id, port, path))

        logger.info(f"Running topology...")
        runner.run(terminate_on_complete=True)
        runner.close()
        logger.info(f"Ran topology")

    if args.export_path:
        suffix = os.path.splitext(args.export_path)[1]
        try:
            if suffix == ".zip":
                with open(args.export_path, "wb") as f:
                    t.save_zip(f, include_data=args.export_data)
            elif suffix == ".yaml" or suffix == ".yml":
                from hyrrokkin.utils.yaml_exporter import export_to_yaml
                export_to_yaml(t, args.export_path, include_data=args.export_data)
            else:
                raise Exception("Unsupported export file type, expecting .zip, .yaml or .yml")
            logger.info(f"Exported topology to {args.export_path}")
        except Exception as ex:
            logger.exception(f"Error exporting topology to {args.export_path}")
            sys.exit(0)


if __name__ == '__main__':
    main()
