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

import threading
from typing import Union, Callable, Literal, Tuple, Any
from threading import Event
import io
import os
import time

from hyrrokkin.utils.type_hints import JsonType
from hyrrokkin.interfaces.topology_api import TopologyApi
from hyrrokkin.engine_launchers.engine_launcher import EngineLauncher
from hyrrokkin.core.topology import Topology as CoreTopology
from hyrrokkin.core.serde import Serde
from hyrrokkin.api.schema_type import SchemaType
from hyrrokkin.interfaces.schema_api import SchemaTypeApi, NodeTypeApi, LinkTypeApi
from hyrrokkin.interfaces.client_api import ClientApi
from hyrrokkin.interfaces.topology_listener_api import TopologyListenerAPI
from hyrrokkin.utils.threadsafe import threadsafe

def check_notclosed(func):
    """
    Decorator that prevents access to a method once the closed attribute is set to True
    :param func: the method to be decorated
    :return: wrapped method
    """

    def notclosed_wrapper(self, *args, **kwargs):
        if self.closed:
            raise Exception("Topology is closed")
        return func(self, *args, **kwargs)

    return notclosed_wrapper


class Topology(TopologyApi):

    def __init__(self, topology_folder: str, package_list: list[str], temporary_folder: str | None = None,
                 engine_launcher: Union[EngineLauncher, None] = None,
                 read_only: bool = False,
                 set_engine_pid_callback: Callable[[int], None] = None,
                 import_from_path: str = None
                 ):
        """
        Create a topology instance

        Args:
            topology_folder: the folder used to store the topology's definition and files
            package_list: a list of the paths to python packages containing hyrrokkin package schemas (a schema.json file)
            temporary_folder: a folder used to store files temporarily during execution
            engine_launcher: the engine_launcher to use to run the topology in a remote process.  if not specified, select an appropriate one
                             for the packages loaded
            read_only: if true, do not allow nodes and configurations to persist data/properties changes to disk when running the topology
            set_engine_pid_callback: function that is called with the process identifier (PID) of the engine process if the engine is launched in a sub-process
            import_from_path: import from this path to initialise the topology
        """
        self.closed = False
        self.paused = True
        self.lock = threading.RLock()
        self.set_engine_pid_callback = set_engine_pid_callback
        self.topology = CoreTopology(topology_folder, package_list)
        self.topology.load_dir()
        self.schema = SchemaType(self.topology.get_schema())
        self.execution_complete_event = Event()
        self.serde = Serde(self.topology.get_schema())

        if import_from_path is not None:
            self.topology.import_from(import_from_path)

        self.temporary_folder = temporary_folder
        self.engine_launcher = engine_launcher
        self.read_only = read_only

        self.runner = None

        self.output_listeners = {}
        self.injected_input_values = {}

        self.listeners: list[TopologyListenerAPI] = []
        self.status_events = {}
        self.execution_events = {}

    def __repr__(self):
        return f"hyrrokkin.api.Topology(#nodes={len(self.get_nodes())},#links={len(self.get_links())})"

    def get_package_path(self, package_id):
        return self.topology.get_schema().get_package_path(package_id)

    def close(self):
        self.closed = True
        if self.runner is not None:
            self.runner.stop()
            self.runner.join()
            self.runner.close()

    # methods implementing the TopologyApi interface

    @check_notclosed
    @threadsafe
    def set_metadata(self, metadata: dict[str, str], ref: str | None = None):
        self.topology.set_metadata(metadata)
        for listener in self.listeners:
            listener.design_metadata_updated(metadata, ref=ref)

    @check_notclosed
    @threadsafe
    def add_node(self, node_id: str | None, node_type: str, metadata: dict[str, JsonType] = {},
                 properties: dict[str, JsonType] = {},
                 data: dict[str, bytes] = {}, copy_from_node_id: str = "", ref: str | None = None) -> str:
        node_id = self.topology.add_node(node_id, node_type, metadata, properties, data, copy_from_node_id)
        for listener in self.listeners:
            listener.node_added(node_id, node_type, metadata, ref=ref)
        return node_id

    @check_notclosed
    @threadsafe
    def update_node_metadata(self, node_id: str | None, metadata: dict[str, JsonType] = {},
                             ref: str | None = None) -> None:
        self.topology.update_node_metadata(node_id, metadata)
        for listener in self.listeners:
            listener.node_metadata_updated(node_id, metadata, ref=ref)

    @check_notclosed
    @threadsafe
    def remove_node(self, node_id: str, ref: str | None = None):
        self.topology.remove_node(node_id)
        for listener in self.listeners:
            listener.node_removed(node_id, ref=ref)

    @check_notclosed
    @threadsafe
    def add_link(self, link_id: str | None, from_node_id: str, from_port: str | None, to_node_id: str,
                 to_port: str | None, ref: str | None = None):
        link_id = self.topology.add_link(link_id, from_node_id, from_port, to_node_id, to_port)
        link_type = self.topology.get_link_type(link_id)
        for listener in self.listeners:
            listener.link_added(link_id, link_type, from_node_id, from_port, to_node_id, to_port, ref=ref)
        return link_id

    @check_notclosed
    @threadsafe
    def remove_link(self, link_id: str, ref: str | None = None):
        self.topology.remove_link(link_id)
        for listener in self.listeners:
            listener.link_removed(link_id, ref=ref)

    @check_notclosed
    @threadsafe
    def clear(self, ref: str | None = None):
        self.topology.clear()
        for listener in self.listeners:
            listener.clear(ref=ref)

    @check_notclosed
    @threadsafe
    def start(self, paused=False, ref: str | None = None):
        self.runner = self.topology.open_runner(self.temporary_folder,
                                                status_event_handler=lambda target_type, target_id, msg,
                                                                            status_code: self.status_event_handler(
                                                    target_type, target_id, msg, status_code),
                                                execution_event_handler=lambda timestamp, node_id, state, error,
                                                                               is_manual: self.execution_event_handler(
                                                    timestamp, node_id, state, error, is_manual),
                                                engine_launcher=self.engine_launcher,
                                                read_only=self.read_only,
                                                paused=True,
                                                set_engine_pid_callback=self.set_engine_pid_callback)
        self.runner.set_execution_complete_callback(lambda: self.execution_complete_handler())
        self.runner.set_request_open_client_callback(
            lambda origin_id, origin_type, session_id, client_name: self.request_open_client(origin_id, origin_type,
                                                                                             session_id, client_name))
        for (node_id, input_port_name) in self.injected_input_values:
            self.runner.inject_input_value(node_id, input_port_name, self.injected_input_values[(node_id, input_port_name)])
        for (node_id, output_port_name) in self.output_listeners:
            self.runner.add_output_listener(node_id, output_port_name, self.output_listeners[(node_id, output_port_name)])

        self.runner.start()

        for listener in self.listeners:
            listener.started(ref=ref)

        self.paused = paused

        if not paused:
            self.runner.resume()
            for listener in self.listeners:
                listener.resumed(ref=ref)

    @check_notclosed
    @threadsafe
    def is_started(self):
        return self.runner is not None

    @check_notclosed
    @threadsafe
    def pause(self, ref: str | None = None):
        if self.paused is False:
            self.paused = True
            if self.runner is not None:
                self.runner.pause()
            for listener in self.listeners:
                listener.paused(ref=ref)

    @check_notclosed
    @threadsafe
    def resume(self, ref: str | None = None):
        if self.paused is True:
            self.paused = False
            if not self.runner:
                self.start(ref)
            else:
                self.runner.resume()
            for listener in self.listeners:
                listener.resumed(ref=ref)

    @check_notclosed
    @threadsafe
    def is_paused(self):
        return self.paused

    @check_notclosed
    @threadsafe
    def restart(self, ref: str | None = None):
        for listener in self.listeners:
            listener.restarting(ref=ref)

        if self.runner:

            self.runner.restart()

            for node_id in self.get_nodes():
                timestamp = time.time()
                state = "pending"
                self.execution_events[node_id] = (timestamp, state, "", False)
                for listener in self.listeners:
                    listener.execution_event(timestamp, node_id, state, "", False)

        for listener in self.listeners:
            listener.restarted(ref=ref)

    @check_notclosed
    def run(self):
        self.resume()
        self.execution_complete_event.wait()
        self.pause()
        with self.lock:
            return self.runner.get_failures()

    @check_notclosed
    def run_task(self, task_name, input_port_values, output_ports, ref: str | None = None, decode_outputs=True):
        if self.runner is None:
            self.start(ref)
        for key in input_port_values:
            node_id = key.split(":")[0]
            input_port_name = key.split(":")[1]
            (package_id, node_type_id) = self.topology.get_node_type(node_id)
            if not isinstance(input_port_values[key],bytes):
                input_port_values[key] = self.serde.serialise(input_port_values[key], package_id, node_type_id, input_port_name)
        with self.lock:
            task_id = self.runner.submit_task(task_name, input_port_values, output_ports)
        (output_values, failures) = self.runner.wait_for_task(task_id)
        for key in output_values:
            node_id = key.split(":")[0]
            output_port_name = key.split(":")[1]
            (package_id, node_type_id) = self.topology.get_node_type(node_id)
            if decode_outputs:
                output_values[key] = self.serde.deserialise(output_values[key], package_id, node_type_id,
                                                          output_port_name)
        return (output_values, failures)

    @check_notclosed
    @threadsafe
    def reload_node(self, node_id: str, properties: JsonType, data: dict[str, bytes], ref: str | None = None):
        if self.runner is not None:
            listeners = self.listeners[:]

            def on_reload():
                for listener in listeners:
                    listener.node_reloaded(node_id, ref=ref)

            self.runner.reload_node(node_id, properties, data, on_reload=on_reload)
        else:
            self.topology.set_node_properties(node_id, properties)
            for key,value in data.items():
                self.topology.set_node_data(node_id, key, value)
            for listener in self.listeners:
                listener.node_reloaded(node_id, ref=ref)

    @check_notclosed
    @threadsafe
    def add_output_listener(self, node_id: str, output_port_name: str, listener: Callable[[Any], None], decode_outputs:bool=True):
        if not decode_outputs:
            self.output_listeners[(node_id, output_port_name)] = listener
            if self.runner is not None:
                self.runner.add_output_listener(node_id, output_port_name, listener)

        else:
            (package_id, node_type_id) = self.topology.get_node_type(node_id)

            def decoding_listener(value):
                value = self.serde.deserialise(value, package_id, node_type_id, output_port_name)
                listener(value)

            self.output_listeners[(node_id, output_port_name)] = decoding_listener

            if self.runner is not None:
                self.runner.add_output_listener(node_id, output_port_name, decoding_listener)

    @check_notclosed
    @threadsafe
    def remove_output_listener(self, node_id: str, output_port_name: str):
        del self.output_listeners[(node_id, output_port_name)]
        if self.runner is not None:
            self.runner.remove_output_listener(node_id, output_port_name)

    @check_notclosed
    @threadsafe
    def inject_input_value(self, node_id: str, input_port_name: str, value: Any):
        (package_id, node_type_id) = self.topology.get_node_type(node_id)

        if not isinstance(value, bytes):
            value = self.serde.serialise(value, package_id, node_type_id, input_port_name)

        self.injected_input_values[(node_id, input_port_name)] = value
        if self.runner is not None:
            self.runner.inject_input_value(node_id, input_port_name, value)

    @check_notclosed
    @threadsafe
    def inject_input_values(self, node_id: str, input_port_name: str, values: list[Any]):
        (package_id, node_type_id) = self.topology.get_node_type(node_id)

        values = [self.serde.serialise(value, package_id, node_type_id, input_port_name)
                  if not isinstance(value,bytes)  else value for value in values]

        self.injected_input_values[(node_id, input_port_name)] = values
        if self.runner is not None:
            self.runner.inject_input_value(node_id, input_port_name, values)

    ####################################################################################################################
    # session and client related

    @check_notclosed
    @threadsafe
    def open_session(self, session_id: str | None = None) -> str:
        if self.runner is None:
            self.start(paused=self.paused)
        return self.runner.open_session(session_id)

    @check_notclosed
    @threadsafe
    def close_session(self, session_id: str):
        if self.runner is None:
            self.start(paused=self.paused)
        self.runner.close_session(session_id)

    @check_notclosed
    @threadsafe
    def attach_node_client(self, node_id: str, session_id: str = "", client_id: str = "",
                           client_options: dict = {}) -> ClientApi:
        if self.runner is None:
            self.start(paused=self.paused)
        return self.runner.attach_node_client(node_id, session_id, client_id, client_options)

    @check_notclosed
    @threadsafe
    def attach_configuration_client(self, package_id: str, session_id: str = "", client_id: str = "",
                                    client_options: dict = {}) -> ClientApi:
        if self.runner is None:
            self.start()
        return self.runner.attach_configuration_client(package_id, session_id, client_id, client_options)

    ####################################################################################################################
    # retrieve node properties and data

    @threadsafe
    def get_node_properties(self, node_id: str) -> dict[str, JsonType]:
        return self.topology.get_node_properties(node_id)

    @threadsafe
    def get_node_data(self, node_id: str, key: str) -> bytes | None:
        return self.topology.get_node_data(node_id, key)

    @threadsafe
    def get_node_data_keys(self, node_id: str) -> list[str]:
        return self.topology.get_node_data_keys(node_id)

    ####################################################################################################################
    # load and save

    def __note_added(self, added_node_ids, added_link_ids, ref):
        for node_id in added_node_ids:
            (package_id, node_type_name) = self.topology.get_node_type(node_id)
            node_type_id = f"{package_id}:{node_type_name}"
            node_metadata = self.topology.get_node_metadata(node_id)
            for listener in self.listeners:
                listener.node_added(node_id, node_type_id, node_metadata, ref=ref)

        for link_id in added_link_ids:
            (from_node_id, from_port_name, to_node_id, to_port_name) = self.topology.get_link(link_id)
            link_type_id = self.topology.get_link_type(link_id)
            for listener in self.listeners:
                listener.link_added(link_id, link_type_id, from_node_id, from_port_name, to_node_id, to_port_name,
                                    ref=ref)

    @threadsafe
    def load(self, from_file: io.BytesIO, include_data: bool = True, ref: str | None = None) -> Tuple[
        list[str], list[str], dict[str, str]]:
        # if the runner has not been created, can load configuration
        # once the runner has been created, the configuration into an engine has been loaded and there is no real way
        # to update it
        (added_node_ids, added_link_ids, node_renamings) = self.topology.load_zip(from_file, include_data=include_data,
                                                                                  include_configuration=(self.runner is None),
                                                                                  include_metadata=(self.get_metadata()=={}))
        self.__note_added(added_node_ids, added_link_ids, ref=ref)
        return (added_node_ids, added_link_ids, node_renamings)

    @threadsafe
    def save(self, to_file: io.BufferedWriter = None, include_data: bool = True):
        return self.topology.save_zip(to_file, include_data)

    @threadsafe
    def import_from(self, from_path: str, include_data: bool = True, ref: str | None = None) -> Tuple[
        list[str], list[str], dict[str, str]]:
        # if the runner has not been created, can load configuration and topology metadata
        # once the runner has been created, the configuration into an engine has been loaded and there is no real way
        # to update it
        if from_path.endswith(".zip"):
            with open(from_path, "rb") as f:
                (added_node_ids, added_link_ids, node_renamings) = self.topology.load_zip(f, include_data=include_data,
                                                                                          include_configuration=(self.runner is None),
                                                                                          include_metadata=(self.get_metadata()=={}))
        else:
            (added_node_ids, added_link_ids, node_renamings) = self.topology.import_from(from_path, include_data,
                                                                                         include_configuration=(self.runner is None),
                                                                                         include_metadata=(self.get_metadata()=={}))

        self.__note_added(added_node_ids, added_link_ids, ref=ref)
        return (added_node_ids, added_link_ids, node_renamings)

    @threadsafe
    def export_to(self, to_path: str, include_data: bool = True):
        to_dir = os.path.split(to_path)[0]
        if to_dir:
            os.makedirs(to_dir, exist_ok=True)
        if to_path.endswith(".zip"):
            with open(to_path, "wb") as f:
                self.save(f, include_data=include_data)
        else:
            self.topology.export_to(to_path, include_data)

    @threadsafe
    def serialise(self):
        return self.topology.serialise()

    ####################################################################################################################
    # topology introspection

    @threadsafe
    def get_metadata(self) -> dict[str, JsonType]:
        return self.topology.get_metadata()

    @threadsafe
    def get_nodes(self) -> dict[str, NodeTypeApi]:
        nodes = {}
        for node_id, node in self.topology.get_nodes().items():
            node_type = node.get_node_type()
            package_id, node_type_id = node_type.split(":")
            nodes[node_id] = self.schema.get_packages()[package_id].get_node_types()[node_type_id]
        return nodes

    @threadsafe
    def get_links(self) -> dict[str, tuple[LinkTypeApi, str, str]]:
        links = {}
        for link_id, link in self.topology.get_links().items():
            link_type = link.get_link_type()
            from_port_id = link.from_node_id + ":" + link.from_port
            to_port_id = link.to_node_id + ":" + link.to_port
            links[link_id] = (link_type, from_port_id, to_port_id)
        return links

    @threadsafe
    def get_link_ids_for_node(self, node_id: str) -> list[str]:
        return self.topology.get_link_ids_for_node(node_id)

    ####################################################################################################################
    # schema introspection

    @threadsafe
    def get_schema(self) -> SchemaTypeApi:
        return self.schema

    ####################################################################################################################
    # listeners

    def attach_listener(self, listener: TopologyListenerAPI) -> None:
        self.listeners.append(listener)
        for (target_type, target_id), (msg, status_code) in self.status_events.items():
            listener.status_event(target_type, target_id, msg, status_code)
        for (node_id, (timestamp, state, error, is_manual)) in self.execution_events.items():
            listener.execution_event(node_id, timestamp, state, error, is_manual)

    def detach_listener(self, listener: TopologyListenerAPI) -> None:
        self.listeners.remove(listener)

    def status_event_handler(self, target_type: Literal["node"] | Literal["configuration"],
                             target_id: str, msg: str,
                             status_code: Literal["error"] | Literal["warning"] | Literal["info"] | Literal["log"]):
        self.status_events[(target_type, target_id)] = (msg, status_code)
        for listener in self.listeners:
            listener.status_event(target_type, target_id, msg, status_code)

    def execution_event_handler(self, timestamp: float | None,
                                node_id: str,
                                state: Literal["pending"] | Literal["running"] | Literal["completed"] | Literal[
                                    "failed"],
                                error: str | None, is_manual: bool) -> None:
        self.execution_events[node_id] = (timestamp, state, error, is_manual)
        for listener in self.listeners:
            listener.execution_event(timestamp, node_id, state, error, is_manual)

    def execution_complete_handler(self):
        for listener in self.listeners:
            listener.execution_completed()
        self.execution_complete_event.set()

    def request_open_client(self, origin_id, origin_type, session_id, client_name):
        for listener in self.listeners:
            listener.request_open_client(origin_id, origin_type, session_id, client_name)

    ####################################################################################################################
    # localisation

    @check_notclosed
    @threadsafe
    def get_type_for_node(self, node_id):
        return self.topology.get_node_type(node_id)

    @check_notclosed
    @threadsafe
    def get_localisation_bundle(self, package_id, for_language=""):
        return self.topology.get_localisation_bundle(package_id, for_language=for_language)
