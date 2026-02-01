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

from abc import abstractmethod

from typing import Union, Dict, List, Protocol

JsonType = Union[Dict[str, "JsonType"], List["JsonType"], str, int, float, bool, None]

class ClientMessageHandler(Protocol):
    def __call__(self, *args: List[Union[str,bytes,JsonType]]): ...

class ClientInterface:

    @abstractmethod
    def get_session_id(self):
        pass

    @abstractmethod
    def get_client_name(self):
        pass

    @abstractmethod
    def get_client_options(self):
        pass

    @abstractmethod
    def send_message(self, *msg: List[Union[str,bytes,JsonType]]):
        """
        Send a message to the client

        Args:
            *msg: the components of the message to send.  Each component may be string, bytes or a JSON-serialisable value

        """
        pass

    @abstractmethod
    def set_message_handler(self, message_handler:ClientMessageHandler):
        """
        Configure a message handler to be called when messages arrive from the client

        Args:
            message_handler: a function that accepts zero or more message components.  Each component may be string, bytes or a JSON-serialisable value
        """
        pass




