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
import threading

from hyrrokkin_engine_drivers.persistence import Persistence
from .threadsafe import threadsafe


class PersistenceFileSystemSync:

    def __init__(self, target_id, target_type, root_folder):
        self.target_id = target_id
        self.target_type = target_type
        self.root_folder = root_folder
        self.properties = None
        self.lock = threading.RLock()

    @threadsafe
    def get_data(self, key):
        Persistence.check_valid_data_key(key)

        filepath = os.path.join(self.root_folder, self.target_type, self.target_id, "data", key)

        if os.path.exists(filepath):
            with open(filepath, mode="rb") as f:
                return f.read()
        else:
            return None

    @threadsafe
    def get_data_keys(self):
        data_dir = os.path.join(self.root_folder, self.target_type, self.target_id, "data")
        if os.path.exists(data_dir):
            return list(os.listdir(data_dir))
        else:
            return []

    @threadsafe
    def set_data(self, key, data):
        Persistence.check_valid_data_key(key)
        Persistence.check_valid_data_value(data)

        folder = os.path.join(self.root_folder, self.target_type, self.target_id, "data")

        filepath = os.path.join(folder, key)

        if data is None:
            if os.path.exists(filepath):
                os.remove(filepath)
            return

        os.makedirs(folder, exist_ok=True)

        with open(filepath, "wb") as f:
            f.write(data)

    @threadsafe
    def clear_data(self):
        data_dir = os.path.join(self.root_folder, self.target_type, self.target_id, "data")
        if os.path.isdir(data_dir):
            for filename in list(os.listdir(data_dir)):
                os.remove(os.path.join(data_dir, filename))

    @threadsafe
    def get_properties(self):
        if self.properties is None:

            folder = os.path.join(self.root_folder, self.target_type, self.target_id)

            path = os.path.join(folder, "properties.json")
            if os.path.exists(path):
                with open(path) as f:
                    self.properties = json.loads(f.read())
            else:
                self.properties = {}

        return copy.deepcopy(self.properties)

    @threadsafe
    def set_properties(self, properties):
        self.properties = copy.deepcopy(properties)

        folder = os.path.join(self.root_folder, self.target_type, self.target_id)

        path = os.path.join(folder, "properties.json")

        os.makedirs(folder, exist_ok=True)
        with open(path, "w") as f:
            f.write(json.dumps(self.properties))
