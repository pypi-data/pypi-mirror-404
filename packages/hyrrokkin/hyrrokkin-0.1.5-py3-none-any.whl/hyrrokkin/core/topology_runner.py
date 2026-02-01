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
import tempfile
from typing import Callable, Union
import uuid
import threading
import logging
import os

import hyrrokkin.utils.persistence_memory_sync
from hyrrokkin.core.client import Client
from hyrrokkin.execution_manager.execution_manager import ExecutionManager
from hyrrokkin.utils.type_hints import JsonType
from hyrrokkin.execution_manager.execution_client import ExecutionClient
from hyrrokkin.engine_launchers.javascript_engine_launcher import JavascriptEngineLauncher
from hyrrokkin.engine_launchers.python_engine_launcher import PythonEngineLauncher


class TopologyRunner:

    def __init__(self, network, schema, execution_folder, engine_launcher, status_event_handler,
                 execution_event_handler, read_only, paused=True, set_engine_pid_handler=None):

        self.network = network
        self.schema = schema
        if execution_folder is None:
            self.tmp_execution_directory = tempfile.TemporaryDirectory()
            self.execution_folder = self.tmp_execution_directory.name
        else:
            self.execution_folder = execution_folder

        self.engine_launcher = engine_launcher
        self.status_event_handler = status_event_handler
        self.execution_event_handler = execution_event_handler
        self.set_engine_pid_handler = set_engine_pid_handler
        self.read_only = read_only
        self.injected_inputs = {}
        self.output_listeners = {}

        self.closed = False
        self.close_handler = None

        self.logger = logging.getLogger("topology_runner")

        self.add_node_callback = None
        self.add_link_callback = None
        self.remove_node_callback = None
        self.remove_link_callback = None
        self.clear_network_callback = None

        if self.engine_launcher is None:
            # try to work out which engine to run
            for candidate_launcher in [PythonEngineLauncher(), JavascriptEngineLauncher()]:
                valid = True
                for package_id in schema.get_packages():
                    folder = schema.get_package_path(package_id)
                    if not os.path.exists(os.path.join(folder, candidate_launcher.get_configuration_filename())):
                        valid = False
                if valid:
                    self.engine_launcher = candidate_launcher
                    break

        self.paused = paused

        self.thread = None

        for (package_id, package) in self.schema.get_packages().items():
            self.engine_launcher.configure_package(package_id, self.schema.get_package_resource(package_id),
                                                   self.schema.get_package_path(package_id))

        self.execution_clients = {}

        self.session_ids = set()
        self.start_event = None
        self.execution_manager = None
        self.create_executor()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.thread is not None:
            self.stop()
            self.join()
        self.close()

    def create_executor(self):
        self.execution_manager = ExecutionManager(self.schema,
                                                  execution_folder=self.execution_folder,
                                                  status_callback=self.status_event_handler,
                                                  node_execution_callback=self.execution_event_handler,
                                                  engine_launcher=self.engine_launcher,
                                                  read_only=self.read_only,
                                                  client_message_handler=lambda *args: self.__handle_client_message(
                                                      *args),
                                                  properties_update_handler=lambda target_id, target_type, properties:
                                                  self.__handle_properties_update(target_id, target_type, properties),
                                                  data_update_handler=lambda target_id, target_type, key, value:
                                                  self.__handle_data_update(target_id, target_type, key, value),
                                                  paused=True)

        self.execution_manager.set_request_open_client_callback(
            lambda origin_id, origin_type, session_id, client_name: self.__request_open_client(origin_id, origin_type,
                                                                                               session_id, client_name))

        self.open_client_request_handler = None

        self.execution_result = None

        self.execution_manager.init()

        for package_id in self.schema.get_packages():
            dsu = self.network.get_configuration_datastore(package_id)
            self.execution_manager.load_target(package_id, "configuration", dsu)

        for (package_id, package) in self.schema.get_packages().items():
            self.execution_manager.add_package(package_id, package.get_schema(),
                                               self.schema.get_package_path(package_id))

        for node_id in self.network.get_node_ids():
            dsu = self.network.get_node_datastore(node_id)
            self.execution_manager.load_target(node_id, "node", dsu)

        # load all nodes and links into the execution

        for node_id in self.network.get_node_ids():
            self.execution_manager.add_node(self.network.get_node(node_id), copy_from_node_id="")

        for link_id in self.network.get_link_ids():
            self.execution_manager.add_link(self.network.get_link(link_id))

        # listen for further network changes and update the execution accordingly

        self.add_node_callback = self.network.register_add_node_callback(
            lambda node, copy_from_node_id: self.__add_node(node, copy_from_node_id))

        self.add_link_callback = self.network.register_add_link_callback(lambda link: self.__add_link(link))

        self.remove_node_callback = self.network.register_remove_node_callback(
            lambda node: self.__remove_node(node))
        self.remove_link_callback = self.network.register_remove_link_callback(
            lambda link: self.__remove_link(link))

        self.clear_network_callback = self.network.register_clear_network_callback(lambda: self.__clear())

        for ((node_id, output_port_name), listener) in self.output_listeners.items():
            self.execution_manager.add_output_listener(node_id, output_port_name, listener)

        for ((node_id, input_port_name), value) in self.injected_inputs.items():
            self.execution_manager.inject_input_value(node_id, input_port_name, value)

        for session_id in self.session_ids:
            self.execution_manager.open_session(session_id)

        for (target_id, target_type, session_id, client_id) in self.execution_clients:
            client = self.execution_clients[(target_id, target_type, session_id, client_id)]
            self.execution_manager.connect_client(target_id, target_type, session_id, client_id, client)

        if self.set_engine_pid_handler:
            pid = self.execution_manager.get_engine_pid()
            if pid != None:
                self.set_engine_pid_handler(pid)

        if not self.paused:
            self.execution_manager.resume()

    def inject_input_value(self, node_id: str, input_port_name: str, value: Union[bytes, list[bytes]]):
        """
        Inject input values into a node in the topology, via an input port.  The port must not be connected.

        Args:
            node_id: the node id
            input_port_name: the name of the node's input port
            value: the value to inject - encoded as bytes.  For ports that accept multiple connections, a list of bytes may be provided.
        """
        if self.network.get_inputs_to(node_id, input_port_name):
            raise Exception(f"Cannot inject input to connected port {node_id}:{input_port_name}")
        node = self.network.get_node(node_id)
        node_type_id = node.get_node_type()
        node_type = self.schema.get_node_type(node_type_id)
        if isinstance(value, list):
            if not node_type.allow_multiple_input_connections(input_port_name):
                raise Exception(
                    f"injected value for {node_id}:{input_port_name} cannot be a list as port does not accept multiple connections")
        else:
            if node_type.allow_multiple_input_connections(input_port_name):
                raise Exception(
                    f"injected value for {node_id}:{input_port_name} should be a list as port accepts multiple connections")
        self.injected_inputs[(node_id, input_port_name)] = value
        self.execution_manager.inject_input_value(node_id, input_port_name, value)

    def remove_injected_input_value(self, node_id: str, input_port_name: str, value: Union[bytes, list[bytes]]):
        """
        Remove an injected input value from the network.

        Args:
            node_id: the node id
            input_port_name: the name of the node's input port
        """
        if (node_id, input_port_name) in self.injected_inputs:
            del self.injected_inputs[(node_id, input_port_name)]
        self.execution_manager.remove_injected_input(node_id, input_port_name, value)

    def add_output_listener(self, node_id: str, output_port_name: str, listener: Callable[[bytes], None]):
        """
        Listen for values output from a node in the topology.  Replaces any existing listener on the node/port if present.

        Args:
            node_id: the node id
            output_port_name: the name of the node's output port
            listener: a callback function which is invoked with the value on the output port when the node is run
        """
        self.output_listeners[(node_id, output_port_name)] = listener
        self.execution_manager.add_output_listener(node_id, output_port_name, listener)

    def remove_output_listener(self, node_id: str, output_port_name: str):
        """
        Remove a listener from a node/port

        Args:
            node_id: the node id
            output_port_name: the name of the node's output port
        """
        self.execution_manager.remove_output_listener(node_id, output_port_name)

    def open_session(self, session_id: str | None = None) -> str:
        """
        Open a new session

        Args:
            session_id: the identifier of the session or None to generate a new session identifier

        Returns:
            the session identifier for the opened session
        """

        if not session_id:
            session_id = str(uuid.uuid4())

        if session_id not in self.session_ids:
            self.session_ids.add(session_id)
            self.execution_manager.open_session(session_id)
        else:
            self.logger.warning(f"open_session: session {session_id} is already open")

        return session_id

    def close_session(self, session_id: str):
        """
        Close a session

        Args:
            session_id: the identifier of the session to close
        """
        if session_id in self.session_ids:
            self.session_ids.remove(session_id)
            self.execution_manager.close_session(session_id)
        else:
            self.logger.warning(f"open_session: session {session_id} is already open")

    def set_request_open_client_callback(self, open_client_request_handler: Callable[[str, str, str, str], None]):
        """
        Attach a function that will be called when a node requests that a client be attached

        Args:
            open_client_request_handler: function that is called with the origin_id, origin_type, session_id, client_name as parameters
        """
        self.open_client_request_handler = open_client_request_handler

    def set_execution_complete_callback(self, execution_complete_callback: Callable[[], None]):
        """
        Attach a function that will be called whenever execution of the topology completes

        Args:
            execution_complete_callback: function that will be called
        """
        self.execution_manager.set_execution_complete_callback(execution_complete_callback)

    def attach_node_client(self, node_id: str, session_id: str = "", client_id: str = "",
                           client_options: dict = {}) -> Client:
        """
        Attach a client instance to a node.  Any client already attached to the node with the same client_id
        will be detached.

        Args:
            node_id: the node to which the client is to be attached
            session_id: the id of an opened interactive session
            client_id: the name of the client to attach, as defined in the node's schema
            client_options: optional, a dictionary with extra parameters from the client

        Returns:
             an object which implements the Client API and provides methods to interact with the client

        """
        if not session_id or session_id not in self.session_ids:
            session_id = self.open_session(session_id)
        client = Client(lambda: self.detach_node_client(node_id, session_id, client_id), session_id)
        execution_client = ExecutionClient(lambda *args: self.__forward_client_message(*args),
                                           node_id, "node", session_id, client_id, client,
                                           client_options)
        self.execution_clients[(node_id, "node", session_id, client_id)] = execution_client
        self.execution_manager.attach_client(node_id, "node", session_id, client_id, execution_client)
        return client

    def detach_node_client(self, node_id: str, session_id: str, client_id: str):
        """
        Detach a client instance from a node

        Args:
            node_id: the node to which the client is to be attached
            session_id: the id of an opened interactive session
            client_id: the id of the client to detach
        """
        if (node_id, "node", session_id, client_id) in self.execution_clients:
            client = self.execution_clients[(node_id, "node", session_id, client_id)]
            self.execution_manager.detach_client(node_id, "node", session_id, client_id, client)
            del self.execution_clients[(node_id, "node", session_id, client_id)]

    def attach_configuration_client(self, package_id: str, session_id: str = "", client_id: str = "",
                                    client_options: dict = {}) -> Client:
        """
        Attach a client instance to a package configuration

        Args:
            package_id: the package configuration to which the client is to be attached
            session_id: the id of an opened interactive session
            client_id: the id of the client to attach
            client_options: optional, a dictionary with extra parameters for the client

        Returns:
             an object which implements the Client API and provides methods to interact with the client
        """
        if not session_id or session_id not in self.session_ids:
            session_id = self.open_session(session_id)
        client = Client(lambda: self.detach_configuration_client(package_id, session_id, client_id), session_id)
        execution_client = ExecutionClient(lambda *args: self.__forward_client_message(*args),
                                           package_id, "configuration", session_id, client_id, client, client_options)
        self.execution_clients[(package_id, "configuration", session_id, client_id)] = execution_client
        self.execution_manager.attach_client(package_id, "configuration", session_id, client_id, execution_client)
        return client

    def detach_configuration_client(self, package_id: str, session_id: str, client_id):
        """
        Detach a client instance from a package configuration

        Args:
            package_id: the node to which the client is to be attached
            session_id: the id of an opened interactive session
            client_id: the id of the client to detach
        """
        if (package_id, "configuration", session_id, client_id) in self.execution_clients:
            client = self.execution_clients[(package_id, "configuration", session_id, client_id)]
            self.execution_manager.detach_client(package_id, "configuration", session_id, client_id, client)
            del self.execution_clients[(package_id, "configuration", session_id, client_id)]

    def reload_node(self, node_id: str, properties: JsonType, data: dict[str, bytes],
                    on_reload: None | Callable[[], None] = None):
        """
        Reload a node with new properties and data, triggering re-execution of the node and all downstream nodes

        Reloading creates a new instance of the node with the new properties and data

        Args:
            node_id: the id of the node to reload
            properties: the properties to reload
            data: the data to reload
            onreload: callback to invoke when the reload is complete
        """

        def on_stop():
            if self.read_only:
                # don't update the network if this runner is in "read_only" mode
                dsu = hyrrokkin.utils.persistence_memory_sync.PersistenceMemorySync()
            else:
                dsu = self.network.get_node_datastore(node_id)
            dsu.set_properties(properties)
            dsu.clear_data()
            for key, value in data.items():
                dsu.set_data(key, value)
            self.execution_manager.load_target(node_id, "node", dsu)
            self.execution_manager.restart_node(node_id)
            if on_reload:
                on_reload()

        self.execution_manager.stop_node(node_id, on_stop)

    def __handle_client_message(self, target_id, target_type, session_id, client_id, extras):
        if (target_id, target_type, session_id, client_id) in self.execution_clients:
            client = self.execution_clients[(target_id, target_type, session_id, client_id)]
            client.message_callback(*extras)

    def __handle_properties_update(self, target_id, target_type, properties):
        if target_type == "configuration":
            dsu = self.network.get_configuration_datastore(target_id)
        else:
            dsu = self.network.get_node_datastore(target_id)
        dsu.set_properties(properties)

    def __handle_data_update(self, target_id, target_type, key, value):
        if target_type == "configuration":
            dsu = self.network.get_configuration_datastore(target_id)
        else:
            dsu = self.network.get_node_datastore(target_id)
        dsu.set_data(key, value)

    def __forward_client_message(self, target_id, target_type, session_id, client_id, *msg):
        self.execution_manager.forward_client_message(target_id, target_type, session_id, client_id, *msg)

    def __add_node(self, node, copy_from_node_id):
        self.execution_manager.add_node(node, copy_from_node_id)

    def __add_link(self, link):
        # remove any injected input from the port being linked to
        if (link.to_node_id, link.to_port) in self.injected_inputs:
            del self.injected_inputs[(link.to_node_id, link.to_port)]
        self.execution_manager.remove_injected_input_value(link.to_node_id, link.to_port)
        self.execution_manager.add_link(link)

    def __remove_node(self, node):
        self.execution_manager.remove_node(node.get_node_id())

    def __remove_link(self, link):
        self.execution_manager.remove_link(link.get_link_id())

    def __clear(self):
        self.execution_manager.clear()

    def pause(self):
        """
        Pause execution of the topology.  Until resume is called, no new nodes will start running.
        """
        self.paused = True
        self.execution_manager.pause()

    def resume(self):
        """
        Resume execution of the topology
        """
        self.paused = False
        self.execution_manager.resume()

    def is_paused(self):
        """
        Test if the executor is paused

        Returns: True iff the executor is paused

        """
        return self.paused

    def restart(self):
        """
        Restart execution of the topology, by cancelling and then creating a new executor
        """
        try:
            self.execution_manager.cancel()
            self.join()
            self.execution_manager = None
            self.create_executor()
            self.start()
        except:
            self.logger.exception("restart")

    def start(self):
        if self.thread is None:
            self.thread = threading.Thread(target=lambda: self.run(terminate_on_complete=False,
                                                                   resume=not self.paused), daemon=True)
            self.start_event = threading.Event()
            self.thread.start()
            self.start_event.wait()
            self.start_event = None

    def join(self):
        if self.thread is not None:
            self.thread.join()
            self.thread = None

    def run(self, terminate_on_complete: bool = True, resume: bool = True) -> bool:
        """
        Run the execution

        Args:
            terminate_on_complete: if true, terminate the runner as soon as all nodes have finished running
            resume: resume execution if paused
        Returns:
            True iff the execution resulted in no failed nodes
        """
        if self.paused and resume:
            self.resume()

        self.execution_result = self.execution_manager.run(terminate_on_complete=terminate_on_complete,
                                                           start_event=self.start_event)

        return self.execution_result

    def submit_task(self, task_name, input_port_values, output_ports) -> str:
        for input_port_id, value in input_port_values.items():
            comps = input_port_id.split(":")
            node_id = comps[0]
            input_port_name = comps[1]
            node = self.network.get_node(node_id)
            node_type_id = node.get_node_type()
            node_type = self.schema.get_node_type(node_type_id)
            if isinstance(value, list):
                if not node_type.allow_multiple_input_connections(input_port_name):
                    raise Exception(
                        f"injected value for {node_id}:{input_port_name} cannot be a list as port does not accept multiple connections")
            else:
                if node_type.allow_multiple_input_connections(input_port_name):
                    raise Exception(
                        f"injected value for {node_id}:{input_port_name} should be a list as port accepts multiple connections")
            self.injected_inputs[(node_id, input_port_name)] = value
            if self.network.get_inputs_to(node_id, input_port_name):
                raise Exception(f"Cannot inject input to connected port {input_port_id}")

        return self.execution_manager.submit_task(task_name, input_port_values, output_ports)

    def wait_for_task(self, task_id: str):
        return self.execution_manager.wait_for_task(task_id)

    def set_close_callback(self, callback):
        self.close_handler = callback

    def get_result(self):
        return self.execution_result

    def get_failures(self):
        return self.execution_manager.get_failures()

    def stop(self) -> None:
        """
        Stop the current execution, callable from another thread during the execution of run

        Notes:
            the run method will return once any current node executions complete
        """
        if self.execution_manager:
            self.execution_manager.stop()

    def close(self) -> None:
        """
        Close the runner.  After this call returns, no other methods can be called

        :return:
        """
        if self.execution_manager:
            self.execution_manager.close()
            self.execution_manager = None

        # disconnect listeners from the network
        self.add_node_callback = self.network.unregister_add_node_callback(self.add_node_callback)
        self.add_link_callback = self.network.unregister_add_link_callback(self.add_link_callback)
        self.remove_node_callback = self.network.unregister_remove_node_callback(self.remove_node_callback)
        self.remove_link_callback = self.network.unregister_remove_link_callback(self.remove_link_callback)
        self.clear_network_callback = self.network.unregister_clear_network_callback(
            self.clear_network_callback)

        self.closed = True

        if self.close_handler:
            self.close_handler()

    def __request_open_client(self, origin_id, origin_type, session_id, client_id):
        """
        Pass on a request to open a node or configuration client

        Args:
            origin_id:
            origin_type:
            session_id:
            client_id:

        Returns:

        """
        if self.open_client_request_handler is not None:
            self.open_client_request_handler(origin_id, origin_type, session_id, client_id)
