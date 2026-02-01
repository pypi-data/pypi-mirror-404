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

import http.server
import re
import threading
import os
import uuid
import logging
import io

logger=logging.getLogger(__name__)

static_folder = os.path.join(os.path.split(__file__)[0], "..", "static")

from hyrrokkin.service.endpoint import Endpoint
from hyrrokkin.service.topology_endpoint import TopologySession
from hyrrokkin_engine.message_utils import MessageUtils
from hyrrokkin.service.topology_service import TopologyService
from hyrrokkin.service.directory_service import DirectoryService
from hyrrokkin.api.topology import Topology
from hyrrokkin.utils.threadsafe import threadsafe

class DirectorySession:

    def __init__(self, endpoint, sender, session_id, directory_service):
        self.endpoint = endpoint
        self.sender = sender
        self.session_id = session_id
        self.directory_service = directory_service
        self.endpoint.open_directory_session(session_id, self)
        self.directory_service.open_session(session_id)

    def recv(self,msg):
        if msg is None:
            self.close()
        if msg is not None:
            msg_parts = MessageUtils.decode_message(msg)
            self.directory_service.handle_message(*msg_parts, from_session_id=self.session_id)

    def send(self,msg):
        self.sender(msg)

    def close(self):
        self.directory_service.close_session(self.session_id)
        self.endpoint.close_directory_session(self.session_id)


class DirectoryEndpoint(Endpoint):

    def __init__(self, host, port, base_path, topology_directory, start_callback=None):
        super().__init__(host,port,base_path,start_callback=lambda s:start_callback(self))
        self.topology_directory = topology_directory
        self.directory_service = DirectoryService(topology_directory, send_fn=lambda *msg_parts, to_session_id,
                                                                                     except_session_id: self.send_directory_message(
            *msg_parts, to_session_id=to_session_id, except_session_id=except_session_id), base_path=base_path)

        self.lock = threading.RLock()
        self.topologies = {}
        self.topology_services = {}
        self.sessions = {}
        self.directory_sessions = {}

        self.server.attach_handler("GET", self.base_path + "/topology/$topology_id/download",
                                   lambda *args, **kwargs: self.download(*args, **kwargs))
        self.server.attach_ws_handler(self.base_path + "/topology/$topology_id/connect",
                                      lambda *args, **kwargs: self.connect_topology(*args, **kwargs))
        self.server.attach_handler("GET", self.base_path + "/topology/$topology_id/package/$package_id/$$resource",
                                   lambda *args, **kwargs: self.serve_package(*args, **kwargs))

        self.server.attach_ws_handler(self.base_path + "/connect",
                                      lambda *args, **kwargs: self.connect_directory(*args, **kwargs))
        self.server.attach_handler("GET", self.base_path + "/package/$package_id/$$resource",
                                   lambda *args, **kwargs: self.serve_package(*args, **kwargs))
        self.server.attach_handler("GET", self.base_path + "/application/$application_id/application.json",
                                   lambda *args, **kwargs: self.serve_application(*args, **kwargs))
        self.server.attach_handler("GET", self.base_path + "/application/$application_id/package/$package_id/$$resource",
                                   lambda *args, **kwargs: self.serve_package(*args, **kwargs))

        self.server.attach_webroot(self.base_path, static_folder)

    def download(self, path, headers, path_parameters, query_parameters, request_body):
        topology_id = path_parameters["topology_id"]
        topology = self.open_topology(topology_id)
        b = io.BytesIO()
        topology.save(b)
        return (200,b.getvalue(),"application/zip",{})

    def connect_topology(self, session_id, sender, path, path_parameters, query_parameters, headers):
        session_id = str(uuid.uuid4())
        topology_id = path_parameters["topology_id"]
        topology = self.open_topology(topology_id)
        topology_service = self.open_topology_service(topology_id, topology)
        return TopologySession(topology_id, self, sender, session_id, topology_service, directory_url="/topology-directory.html")

    def connect_directory(self, session_id, sender, path, path_parameters, query_parameters, headers):
        session_id = str(uuid.uuid4())
        return DirectorySession(self, sender, session_id, self.directory_service)

    def serve_package(self, path, headers, path_parameters, query_parameters, request_body):
        package_id = path_parameters["package_id"]
        package_path = self.topology_directory.get_package_path(package_id)
        resource_path = path_parameters["resource"]
        path = os.path.join(package_path, resource_path)
        return self.server.serve_file(path)

    def serve_application(self, path, headers, path_parameters, query_parameters, request_body):
        application_id = path_parameters["application_id"]
        application_path = self.topology_directory.get_application_path(application_id)
        return self.server.serve_file(application_path)

    def send_directory_message(self, *msg_parts, to_session_id, except_session_id):
        msg = MessageUtils.encode_message(*msg_parts)
        for session_id in self.directory_sessions:
            if to_session_id is not None:
                if session_id != to_session_id:
                    continue
            if except_session_id is not None:
                if session_id == except_session_id:
                    continue
            self.directory_sessions[session_id].send(msg)

    def send_topology_message(self, to_topology_id, *msg_parts, to_session_id, except_session_id):
        msg = MessageUtils.encode_message(*msg_parts)
        for (topology_id, session_id) in self.sessions:
            if topology_id != to_topology_id:
                continue
            if to_session_id is not None:
                if session_id != to_session_id:
                    continue
            if except_session_id is not None:
                if session_id == except_session_id:
                    continue
            self.sessions[(topology_id, session_id)].send(msg)

    @threadsafe
    def open_directory_session(self, session_id, session):
        self.directory_sessions[session_id] = session

    @threadsafe
    def close_directory_session(self, session_id):
        del self.directory_sessions[session_id]

    def open_topology(self, topology_id):
        if topology_id not in self.topologies:
            self.topologies[topology_id] = Topology(topology_folder=self.topology_directory.get_topology_folder(topology_id),
                            package_list=self.topology_directory.get_packages())
        return self.topologies[topology_id]

    def open_topology_service(self, topology_id, topology):
        if topology_id not in self.topology_services:
            self.topology_services[topology_id] = TopologyService(topology, send_fn=lambda *msg_parts, to_session_id,
                                                           except_session_id: self.send_topology_message(topology_id,
                                                                                                         *msg_parts,
                                                                                                         to_session_id=to_session_id,
                                                                                                         except_session_id=except_session_id),
                                                    design_metadata_update_callback=None, download_url="", base_path=self.base_path)
        return self.topology_services[topology_id]

    def close_topology_service(self, topology_id):
        if topology_id in self.topology_services:
            del self.topology_services[topology_id]

    @threadsafe
    def open_topology_session(self, topology_id, session_id, session):
        self.sessions[(topology_id, session_id)] = session

    @threadsafe
    def close_topology_session(self, topology_id, session_id):
        del self.sessions[(topology_id, session_id)]


