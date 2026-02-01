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

from .wrapper import Wrapper

class NodeWrapper(Wrapper):

    def __init__(self, data_store_utils, node_id, package_id, services, get_configuration_wrapper_fn, set_status_cb,
                 set_execution_state_cb, request_run_cb, send_message_cb, request_open_client_cb, get_connection_count_cb):
        super().__init__(data_store_utils, services, send_message_cb, request_open_client_cb)
        self.node_id = node_id
        self.package_id = package_id
        self.configuration = None
        self.logger = logging.getLogger(f"NodeWrapper[{node_id}]")
        self.services.wrapper = self
        self.get_configuration_wrapper_fn = get_configuration_wrapper_fn
        self.set_status_cb = set_status_cb
        self.set_execution_state_cb = set_execution_state_cb
        self.request_run_cb = request_run_cb
        self.get_connection_count_cb = get_connection_count_cb
        self.active = True

    def get_id(self):
        return self.node_id

    def get_type(self):
        return "node"

    def is_active(self):
        return self.active

    def reactivate(self):
        self.active = True

    def __repr__(self):
        return f"NodeWrapper({self.node_id})"

    async def reset_run(self):
        try:
            if hasattr(self.instance, "reset_run"):
                if inspect.iscoroutinefunction(self.instance.reset_run):
                    await self.instance.reset_run()
                else:
                    self.instance.reset_run()
        except:
            self.logger.exception(f"Error in reset_run for node {self.node_id}")

    async def execute(self, inputs):
        # note - any exceptions raised in the node instance's run method will be caught by the caller
        if self.active:
            if hasattr(self.instance, "run"):
                if inspect.iscoroutinefunction(self.instance.run):
                    result = await self.instance.run(inputs)
                    if self.active:
                        return result
                else:
                    return self.instance.run(inputs)
        else:
            return {}

    def set_status(self, state, status_message):
        self.set_status_cb(status_message, state)

    def set_running_state(self, new_state):
        self.set_execution_state_cb(new_state, True)

    async def request_run(self):
        await self.request_run_cb()

    def get_configuration_wrapper(self, package_id=None):
        return self.get_configuration_wrapper_fn(self.package_id if package_id is None else package_id)

    async def remove(self):
        try:
            if hasattr(self.instance, "remove"):
                if inspect.iscoroutinefunction(self.instance.remove):
                    await self.instance.remove()
                else:
                    self.instance.remove()
        except:
            self.logger.exception(f"Error in remove for {str(self)}")

    def get_connection_count(self, port_name, port_direction):
        return self.get_connection_count_cb(port_name, port_direction)

    async def stop_node(self):
        self.active = False
        self.services.deactivate()
        await self.reset_run()
        await self.remove()











