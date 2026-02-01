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

from hyrrokkin.utils.type_hints import JsonType, MessageHandler
from abc import abstractmethod, ABC

from hyrrokkin.utils.type_hints import JsonType


class ClientApi(ABC):

    @abstractmethod
    def get_session_id(self):
        """
        Get this client's session_id

        Returns:
            the session_id of the session in which this client was opened
        """

    @abstractmethod
    def send_message(self, *msg: bytes | str | JsonType):
        """
        Send a message to the node or configuration

        Args:
            *msg: one or more component parts to the message, must be strings, bytes or json-serializable values
        """

    @abstractmethod
    def set_message_handler(self, message_handler: MessageHandler):
        """
        Set a handler function that is called when a message is received from the node or configuration

        Args:
            message_handler: a function that receives the message as one or more component parts, which may be strings, bytes or json-serializable values
        """

    @abstractmethod
    def close(self):
        """
        Close this client, detaching it from tne node or configuration
        """
