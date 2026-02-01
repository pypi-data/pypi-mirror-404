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

import argparse
import json
import logging
import os

from jsonschema import validate

logger = logging.getLogger("package_validation")

with open(os.path.join(os.path.split(__file__)[0], "topology_schema.json")) as f:
    schema = json.loads(f.read())


def validate_topology(content):
    validate(content, schema)


def validate_topology_yaml_from_path(path):
    with open(path) as f:
        try:
            from yaml import load, FullLoader
            topology = load(f, Loader=FullLoader)
            logger.info(f"Validating: {path}")
            validate_topology(topology)
            logger.info(f"Validated: {path}")
            return True
        except:
            logger.exception(f"Validation failed for: {path}")
            return False


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    args = parser.parse_args()
    validate_topology_yaml_from_path(args.input_file)


if __name__ == '__main__':
    main()
