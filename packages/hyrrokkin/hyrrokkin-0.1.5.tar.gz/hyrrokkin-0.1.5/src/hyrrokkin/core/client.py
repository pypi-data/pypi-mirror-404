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

from hyrrokkin.interfaces.client_api import ClientApi
from hyrrokkin.utils.type_hints import JsonType, MessageHandler


class Client(ClientApi):

    def __init__(self, close_cb, session_id):
        self.close_cb = close_cb
        self.session_id = session_id
        self.message_forwarder = None
        self.message_handler = None
        self.pending_messages = []  # messages to the node that cannot yet be delivered without a message handler
        self.is_open = False
        self.logger = None

    def get_session_id(self):
        """
        Get this client's session_id

        Returns:
            the session_id of the session in which this client was opened
        """
        return self.session_id

    def get_logger(self):
        if self.logger is None:
            self.logger = logging.getLogger(f"Client[{self.session_id}]")
        return self.logger

    def open(self, message_forwarder):
        self.message_forwarder = message_forwarder
        self.is_open = True

    def send_message(self, *msg: bytes | str | JsonType):
        """
        Send a message to the node or configuration

        Args:
            *msg: one or more component parts to the message, must be strings, bytes or json-serializable values
        """
        if self.is_open:
            self.message_forwarder(*msg)
            return True
        return False

    def set_message_handler(self, message_handler: MessageHandler):
        """
        Set a handler function that is called when a message is received from the node or configuration

        Args:
            message_handler: a function that receives the message as one or more component parts, which may be strings, bytes or json-serializable values
        """
        if self.is_open:
            self.message_handler = message_handler
            if self.message_handler:
                for message in self.pending_messages:
                    try:
                        self.message_handler(*message)
                    except Exception as ex:
                        self.get_logger().exception("message_handler")
                self.pending_messages = []

    def handle_message(self, *message):
        if self.is_open:
            if self.message_handler:
                try:
                    self.message_handler(*message)
                except Exception as ex:
                    self.get_logger().exception("message_handler")
            else:
                self.pending_messages.append(message)

    def close(self):
        self.is_open = False
        self.message_forwarder = None
        self.close_cb()
