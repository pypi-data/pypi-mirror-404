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


import logging


class DirectoryService:

    package_metadata = []

    def __init__(self, topology_directory, send_fn, base_path=""):
        self.logger = logging.getLogger("DirectoryService")
        self.topology_directory = topology_directory
        self.package_urls = []
        self.base_path = base_path
        for package_id in self.topology_directory.get_package_ids():
            self.package_urls.append(f"package/{package_id}")
        self.send_fn = send_fn

    def send(self, *msg_parts, to_session_id=None, except_session_id=None):
        self.send_fn(*msg_parts, to_session_id=to_session_id, except_session_id=except_session_id)

    def handle_message(self, msg, from_session_id):
        o = msg
        if o["action"] == "remove_topology":
            topology_id = o["topology_id"]
            self.topology_directory.remove_topology(topology_id)
            self.send(msg, to_session_id=None, except_session_id=from_session_id)
        elif o["action"] == "create_topology":
            topology_id = o["topology_id"]
            from_topology_id = o.get("from_topology_id", None)
            o["metadata"] = self.topology_directory.create_topology(topology_id, from_topology_id)
            o["status"] = {"running": False}
            self.send(msg, to_session_id=None, except_session_id=from_session_id)
        elif o["action"] == "reload_topology":
            topology_id = o["topology_id"]
            self.topology_directory.reload_topology(topology_id)

    def open_session(self, sid, user_id=None):
        # identify which topologies have a template
        topologies = self.topology_directory.get_topologies()
        templates = self.topology_directory.get_templates()

        if templates:
            for topology_id in topologies:
                if topology_id in templates:
                    topologies[topology_id]["metadata"]["has_template"] = True

        applications = self.topology_directory.get_applications()
        state = {"action": "init", "topologies": topologies, "applications": applications,
                 "package_urls": self.package_urls, "base_path": self.base_path}

        self.send(state, to_session_id=sid, except_session_id=None)

    def close_session(self, sid):
        pass
