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
import inspect
from importlib import import_module

from hyrrokkin_engine.client import Client

class Wrapper:

    def __init__(self, datastore_utils, services, send_message_cb, request_open_client_cb):
        self.datastore_utils = datastore_utils
        self.instance = None
        self.clients = {}
        self.services = services
        self.services.set_wrapper(self)
        self.logger = logging.getLogger("NodeWrapper")
        self.send_message_cb = send_message_cb
        self.request_open_client_cb = request_open_client_cb

    def get_id(self):
        # override in subclass
        raise NotImplementedError()

    def get_type(self):
        # override in subclass
        raise NotImplementedError()

    def set_service(self, service):
        self.services = service

    async def set_instance(self, instance):
        self.instance = instance
        await self.load()

    async def load(self):
        if hasattr(self.instance, "load"):
            try:
                if inspect.iscoroutinefunction(self.instance.load):
                    await self.instance.load()
                else:
                    self.instance.load()
            except:
                self.logger.exception(f"Error in load for {self.get_id()}")

    def get_instance(self):
        return self.instance

    async def get_properties(self):
        return await self.datastore_utils.get_properties()

    async def set_properties(self, properties):
        await self.datastore_utils.set_properties(properties)

    async def get_data(self, key):
        return await self.datastore_utils.get_data(key)

    async def set_data(self, key, data):
        await self.datastore_utils.set_data(key, data)

    async def get_data_keys(self):
        return await self.datastore_utils.get_data_keys()

    def request_open_client(self, client_name, session_id):
        if self.request_open_client_cb:
            self.request_open_client_cb(client_name, session_id)

    async def open_client(self, session_id, client_id, client_options):
        def message_forwarder(*message_parts):
            # send a message to a client
            self.send_message_cb(session_id, client_id, *message_parts)
        try:
            if hasattr(self.instance, "open_client"):
                client = Client(session_id, client_id, client_options)
                client.open(message_forwarder)
                self.clients[(session_id,client_id)] = client
                if inspect.iscoroutinefunction(self.instance.open_client):
                    await self.instance.open_client(client)
                else:
                    self.instance.open_client(client)
        except:
            self.logger.exception(f"Error in open_client for {str(self)}")

    async def recv_message(self, session_id, client_id, *message):
        key = (session_id, client_id)
        if key in self.clients:
            await self.clients[key].handle_message(*message)
        else:
            self.logger.error(f"No client for message sent to session_id={session_id} and client_id={client_id}")

    async def close_client(self, session_id, client_id):
        key = (session_id, client_id)
        if key in self.clients:
            client = self.clients[key]
            try:
                if hasattr(self.instance, "close_client"):
                    if inspect.iscoroutinefunction(self.instance.close_client):
                        await self.instance.close_client(client)
                    else:
                        self.instance.close_client(client)
            except:
                self.logger.exception(f"Error in close_client for {str(self)}")
            client.close()
            del self.clients[key]

    @staticmethod
    def get_class(module_class_name):
        module_path, class_name = module_class_name.rsplit('.', 1)
        module = import_module(module_path)
        cls = getattr(module, class_name)
        return cls

