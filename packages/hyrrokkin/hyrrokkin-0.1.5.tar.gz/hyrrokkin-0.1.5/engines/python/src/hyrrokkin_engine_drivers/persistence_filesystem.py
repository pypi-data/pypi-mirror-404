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
import copy

from .persistence import Persistence

class PersistenceFileSystem(Persistence):

    def __init__(self, root_folder, read_only):
        super().__init__()
        self.root_folder = root_folder
        self.properties = None
        self.data_cache = {}
        self.read_only = read_only

    async def get_data(self, key):
        Persistence.check_valid_data_key(key)

        if key in self.data_cache:
            return self.data_cache[key]

        filepath = os.path.join(self.root_folder, self.target_type, self.target_id, "data", key)

        if os.path.exists(filepath):
            with open(filepath, mode="rb") as f:
                return f.read()
        else:
            return None

    async def get_data_keys(self):
        data_dir = os.path.join(self.root_folder, self.target_type, self.target_id, "data")
        if os.path.exists(data_dir):
            return list(os.listdir(data_dir))
        else:
            return []

    async def set_data(self, key, data):

        Persistence.check_valid_data_key(key)
        Persistence.check_valid_data_value(data)

        if self.read_only:
            if data is None:
                if key in self.data_cache:
                    del self.data_cache[key]
            else:
                self.data_cache[key] = data

        else:
            folder = os.path.join(self.root_folder, self.target_type, self.target_id, "data")

            filepath = os.path.join(folder, key)

            if data is None:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return

            os.makedirs(folder, exist_ok=True)

            with open(filepath, "wb") as f:
                f.write(data)

        self.data_updated(key, data)


    async def set_properties(self, properties):
        self.properties = copy.deepcopy(properties)
        if self.read_only:
            return

        folder = os.path.join(self.root_folder, self.target_type, self.target_id)

        path = os.path.join(folder, "properties.json")

        os.makedirs(folder, exist_ok=True)
        with open(path,"w") as f:
            f.write(json.dumps(self.properties))
        self.properties_updated(properties)

    async def get_properties(self):
        if self.properties is None:
            folder = os.path.join(self.root_folder, self.target_type, self.target_id)

            path = os.path.join(folder, "properties.json")
            if os.path.exists(path):
                with open(path) as f:
                    self.properties = json.loads(f.read())
            else:
                self.properties = {}

        return self.properties



