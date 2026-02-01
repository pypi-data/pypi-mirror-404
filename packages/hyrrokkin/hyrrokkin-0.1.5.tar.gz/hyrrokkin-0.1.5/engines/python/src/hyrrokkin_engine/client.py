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

class Client:

    def __init__(self, session_id, client_id, client_options):
        self.session_id = session_id;
        self.client_id = client_id;
        self.client_options = client_options
        self.message_forwarder = None
        self.message_handler = None
        self.is_open = False
        self.logger = None

    def get_session_id(self):
        return self.session_id

    def get_client_name(self):
        return self.client_id.split("@")[0];

    def get_client_options(self):
        return self.client_options

    def get_logger(self):
        if self.logger is None:
            self.logger = logging.getLogger("Client")
        return self.logger

    def open(self, message_forwarder):
        self.message_forwarder = message_forwarder
        self.is_open = True

    def send_message(self, *msg):
        if self.is_open:
            self.message_forwarder(*msg)
        else:
            raise Exception("cannot send message, client is closed")

    def set_message_handler(self, message_handler):
        self.message_handler = message_handler
        self.message_handler_isasync = inspect.iscoroutinefunction(message_handler) if message_handler is not None else False

    async def handle_message(self, *message):
        if self.message_handler is not None:
            try:
                if self.message_handler_isasync:
                    await self.message_handler(*message)
                else:
                    self.message_handler(*message)
            except Exception as ex:
                self.get_logger().exception("message_handler")
        else:
            self.get_logger().warning("no message_handler")

    def close(self):
        self.is_open = False
        self.message_forwarder = None

