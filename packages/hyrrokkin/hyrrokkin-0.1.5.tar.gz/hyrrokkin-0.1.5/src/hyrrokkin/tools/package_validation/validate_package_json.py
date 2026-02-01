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

with open(os.path.join(os.path.split(__file__)[0], "package_schema.json")) as f:
    schema = json.loads(f.read())


def validate_package_schema(json_content):
    o = json.loads(json_content)
    validate(o, schema)


def validate_package_schema_from_path(path_to_json):
    with open(path_to_json) as f:
        try:
            logger.info(f"Validating: {path_to_json}")
            validate_package_schema(f.read())
            logger.info(f"Validated: {path_to_json}")
            return True
        except:
            logger.exception(f"Validation failed for: {path_to_json}")
            return False


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    args = parser.parse_args()
    validate_package_schema_from_path(args.input_file)


if __name__ == '__main__':
    main()
