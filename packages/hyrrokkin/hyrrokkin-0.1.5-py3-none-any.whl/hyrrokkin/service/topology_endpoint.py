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
import uuid
import io
import logging
import threading

import mimetypes

from hyrrokkin.service.endpoint import Endpoint

static_folder = os.path.join(os.path.split(__file__)[0], "..", "static")

from hyrrokkin.service.topology_service import TopologyService
from hyrrokkin_engine.message_utils import MessageUtils
from hyrrokkin.utils.threadsafe import threadsafe

logger=logging.getLogger(__name__)


class TopologySession:

    def __init__(self, topology_id, endpoint, sender, session_id, topology_service, directory_url=None):
        self.topology_id = topology_id
        self.endpoint = endpoint
        self.sender = sender
        self.session_id = session_id
        self.topology_service = topology_service
        self.endpoint.open_topology_session(topology_id, session_id, self)
        self.topology_service.open_session(session_id, directory_url=directory_url)

    def recv(self,msg):
        if msg is None:
            self.close()
        if msg is not None:
            msg_parts = MessageUtils.decode_message(msg)
            self.topology_service.handle_message(*msg_parts, from_session_id=self.session_id)

    def send(self,msg):
        self.sender(msg)

    def close(self):
        self.topology_service.close_session(self.session_id)
        self.endpoint.close_topology_session(self.topology_id, self.session_id)


class TargetSession:

    def __init__(self, topology_id, endpoint, sender, session_id, topology_service, target_type, target_id, page_id, language_id):
        self.topology_id = topology_id
        self.endpoint = endpoint
        self.sender = sender
        self.session_id = session_id
        self.topology_service = topology_service
        self.target_type = target_type
        self.target_id = target_id
        self.page_id = page_id
        self.logger = logging.getLogger("NodeSession")
        # self.endpoint.open_topology_session(topology_id, session_id, self)
        # self.topology_service.open_session(session_id)
        if self.target_type == "node":
            self.client = self.topology_service.open_node_client(node_id=self.target_id, from_session_id=session_id, client_id=page_id, client_options={})
        else:
            self.client = self.topology_service.open_configuration_client(package_id=self.target_id, from_session_id=session_id,
                                                                 client_id=page_id, client_options={})
        def message_handler(*msg):
            enc_msg = MessageUtils.encode_message(*[{"type":"page_message"},msg])
            self.send(enc_msg)
        self.client.set_message_handler(message_handler)
        if self.target_type == "node":
            language_code, bundle = self.topology_service.get_localisation_bundle_for_node(node_id=self.target_id, for_language=language_id)
        else:
            language_code, bundle = self.topology_service.get_localisation_bundle_for_package(package_id=self.target_id,
                                                                                           for_language=language_id)
        self.send(MessageUtils.encode_message({"type":"page_init","language":language_code,"bundle":bundle}))

    def recv(self,msg):
        if msg is None:
            self.close()
        if msg is not None:
            msg_parts = MessageUtils.decode_message(msg)
            header = msg_parts[0]
            if header["type"] == "page_message":
                self.client.send_message(msg_parts[1:])
            else:
                self.logger.error("Unknown message type")

    def send(self,msg):
        self.sender(msg)

    def close(self):
        if self.target_type == "node":
            self.topology_service.close_node_client(self.target_id, self.session_id, self.page_id)
        else:
            self.topology_service.close_configuation_client(self.node_id, self.session_id, self.page_id)
        # self.topology_service.close_session(self.session_id)
        # self.endpoint.close_node_session(self.node_id, self.session_id, self.page_id)


class TopologyEndpoint(Endpoint):

    def __init__(self, host, port, base_path, topology, download_url="/download", start_callback=None):
        super().__init__(host, port, base_path, start_callback=lambda s:start_callback(self))

        self.topology = topology
        self.topology_id = "topology"

        self.topology_service = TopologyService(topology,
                                                lambda *msg_parts, to_session_id, except_session_id: self.send_message(
                                                    self.topology_id, *msg_parts, to_session_id=to_session_id,
                                                    except_session_id=except_session_id), download_url=download_url, base_path=base_path)
        self.sessions = {}
        self.lock = threading.RLock()

        self.server.attach_handler("GET", self.base_path + "/download", lambda *args, **kwargs: self.download(*args, **kwargs))
        self.server.attach_ws_handler(self.base_path + "/connect",
                                   lambda *args, **kwargs: self.connect(*args, **kwargs))
        self.server.attach_ws_handler(self.base_path + "/node/$node_id/$page_id/$language_id/connect",
                                      lambda *args, **kwargs: self.connect_target("node",*args, **kwargs))
        self.server.attach_ws_handler(self.base_path + "/node/$node_id/$page_id/connect",
                                      lambda *args, **kwargs: self.connect_target("node",*args, **kwargs))
        self.server.attach_ws_handler(self.base_path + "/configuration/$package_id/$page_id/$language_id/connect",
                                      lambda *args, **kwargs: self.connect_target("configuration", *args, **kwargs))
        self.server.attach_ws_handler(self.base_path + "/configuration/$package_id/$page_id/connect",
                                      lambda *args, **kwargs: self.connect_target("configuration", *args, **kwargs))
        self.server.attach_handler("GET", self.base_path + "/package/$package_id/$$resource",
                               lambda *args, **kwargs: self.serve_package(*args, **kwargs))
        self.server.attach_webroot(self.base_path, static_folder)

    def download(self, path, headers, path_parameters, query_parameters, request_body):
        b = io.BytesIO()
        self.topology.save(b)
        return (200,b.getvalue(),"application/zip",{})

    def connect(self, session_id, sender, path, path_parameters, query_parameters, headers):
        session_id = str(uuid.uuid4())
        s = TopologySession(self.topology_id, self, sender, session_id, self.topology_service)
        return s

    def connect_target(self, target_type, session_id, sender, path, path_parameters, query_parameters, headers):
        session_id = str(uuid.uuid4())
        target_id = path_parameters.get("node_id",path_parameters.get("package_id"))
        page_id = path_parameters["page_id"]
        language_id = path_parameters.get("language_id","")
        s = TargetSession(self.topology_id, self, sender, session_id, self.topology_service, target_type=target_type, target_id=target_id, page_id=page_id, language_id=language_id)
        return s

    def serve_package(self, path, headers, path_parameters, query_parameters, request_body):
        package_id = path_parameters["package_id"]
        package_path = self.topology.get_package_path(package_id)
        resource_path = path_parameters["resource"]
        path = os.path.join(package_path, resource_path)
        return self.server.serve_file(path)

    @threadsafe
    def open_topology_session(self, topology_id, session_id, session):
        self.sessions[(topology_id,session_id)] = session

    @threadsafe
    def close_topology_session(self, topology_id, session_id):
        del self.sessions[(topology_id, session_id)]

    def send_message(self, to_topology_id, *msg_parts, to_session_id, except_session_id):
        msg = MessageUtils.encode_message(*msg_parts)
        for (topology_id,session_id) in self.sessions:
            if topology_id != to_topology_id:
                continue
            if to_session_id is not None:
                if session_id != to_session_id:
                    continue
            if except_session_id is not None:
                if session_id == except_session_id:
                    continue
            self.sessions[(topology_id,session_id)].send(msg)




