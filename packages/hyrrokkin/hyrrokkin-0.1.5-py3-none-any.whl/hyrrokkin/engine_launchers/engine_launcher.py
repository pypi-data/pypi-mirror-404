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

from typing import Literal


class EngineLauncher:

    def __init__(self, persistence: Literal["memory", "filesystem"], verbose: bool = False):
        self.persistence = persistence
        self.verbose = verbose

    def track_output(self, output):
        if self.verbose:
            print(f"[engine] {output}")

    def get_name(self):
        pass

    def __repr__(self):
        return self.get_name()

    def get_commandline(self, host_name, port):
        pass

    def get_inputs(self):
        yield from []

    def configure_package(self, resource_path, package_folder):
        pass

    def get_worker_configuration(self):
        pass

    def get_language(self):
        pass

    def get_persistence(self) -> Literal["memory", "filesystem"]:
        return self.persistence
