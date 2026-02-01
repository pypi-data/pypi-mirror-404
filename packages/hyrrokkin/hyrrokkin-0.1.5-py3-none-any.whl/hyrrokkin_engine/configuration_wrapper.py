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

from .wrapper import Wrapper

class ConfigurationWrapper(Wrapper):

    def __init__(self, data_store_utils, package_id, services, get_configuration_wrapper_fn, set_status_cb, send_message_cb, request_open_client_cb):
        super().__init__(data_store_utils, services, send_message_cb, request_open_client_cb)
        self.package_id = package_id
        self.message_handler = None
        self.logger = logging.getLogger(f"ConfigurationWrapper[{package_id}]")
        self.get_configuration_wrapper_fn = get_configuration_wrapper_fn
        self.set_status_cb = set_status_cb

    def get_id(self):
        return self.package_id

    def get_type(self):
        return "configuration"

    def __repr__(self):
        return f"ConfigurationWrapper({self.package_id})"

    def set_status(self, state, status_message):
        self.set_status_cb(status_message, state)

    async def create_node(self, node_type_id, node_services):
        if hasattr(self.instance, "create_node"):
            try:
                return await self.instance.create_node(node_type_id, node_services)
            except:
                self.logger.exception(f"Error in create_node for {node_type_id}")

    def get_configuration_wrapper(self, package_id):
        return self.get_configuration_wrapper_fn(package_id)

    def open_session(self, session_id):
        if hasattr(self.instance, "open_session"):
            try:
                self.instance.open_session(session_id)
            except:
                self.logger.exception(f"Error in open_session for {str(self)}")

    def close_session(self, session_id):
        if hasattr(self.instance, "close_session"):
            try:
                self.instance.close_session(session_id)
            except:
                self.logger.exception(f"Error in close_session for {str(self)}")

    def encode(self, value, link_type):
        if hasattr(self.instance, "encode"):
            try:
                return self.instance.encode(value, link_type)
            except:
                self.logger.exception(f"Error in encode for link_type={link_type}")
        return None

    def decode(self, encoded_bytes, link_type):
        if hasattr(self.instance, "decode"):
            try:
                return self.instance.decode(encoded_bytes, link_type)
            except:
                self.logger.exception(f"Error in decode for link_type={link_type}")
        return None

