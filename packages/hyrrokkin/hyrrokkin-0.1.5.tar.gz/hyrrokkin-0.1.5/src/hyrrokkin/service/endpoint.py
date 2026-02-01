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
import threading

import mimetypes


from moonlette.server import Server as MoonletteServer

static_folder = os.path.join(os.path.split(__file__)[0], "..", "static")


class Endpoint(threading.Thread):

    def __init__(self, host, port, base_path, start_callback=None):
        super().__init__()
        self.daemon = False
        self.host = host
        self.port = port
        self.base_path = base_path
        self.server = MoonletteServer(host=self.host, port=self.port, base_url=self.base_path)
        self.start_callback = start_callback

    def run(self):
        self.server.run(callback=lambda ok: self.start_callback(self.server) if self.start_callback is not None else None)

    def check_running(self):
        return self.server.check_running()

    def stop(self):
        self.server.close()


