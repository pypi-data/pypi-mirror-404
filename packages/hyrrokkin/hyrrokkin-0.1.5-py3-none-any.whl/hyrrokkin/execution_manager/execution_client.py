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


class ExecutionClient():

    def __init__(self, forward_client_message_callback, target_id, target_type, session_id, client_id, client,
                 client_options):
        self.forward_client_message_callback = forward_client_message_callback
        self.target_id = target_id
        self.target_type = target_type  # node or configuration
        self.session_id = session_id
        self.client_id = client_id
        self.client = client
        self.client_options = client_options
        self.client.open(lambda *msg: self.send_message(*msg))
        self.pending_messages = []
        self.connected = False

    def set_connected(self):
        self.connected = True
        for message in self.pending_messages:
            self.forward_client_message_callback(self.target_id, self.target_type, self.session_id, self.client_id,
                                                 *message)
        self.pending_messages = []

    def send_message(self, *msg):
        # send a message to the configuration or node
        if self.connected:
            self.forward_client_message_callback(self.target_id, self.target_type, self.session_id, self.client_id,
                                                 *msg)
        else:
            self.pending_messages.append(msg)

    def message_callback(self, *msg):
        self.client.handle_message(*msg)

    def disconnect(self):
        self.execution_thread = None

    def get_client_options(self):
        return self.client_options
