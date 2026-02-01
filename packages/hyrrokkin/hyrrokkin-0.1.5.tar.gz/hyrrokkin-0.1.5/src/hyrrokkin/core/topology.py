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

import io
import os
import logging
from typing import Union, Dict, Callable

from hyrrokkin.utils.type_hints import JsonType

from hyrrokkin.core.schema import Schema
from hyrrokkin.model.node import Node
from hyrrokkin.model.link import Link
from hyrrokkin.exceptions.invalid_link_error import InvalidLinkError
from hyrrokkin.exceptions.invalid_node_error import InvalidNodeError

from hyrrokkin.model.network import Network
from hyrrokkin.core.topology_runner import TopologyRunner
from hyrrokkin.engine_launchers.engine_launcher import EngineLauncher


class Topology:

    def __init__(self, execution_folder: str, package_list: list[str]):
        """
        Create a topology

        Args:
            execution_folder: the folder used to store the topology definition and files
            package_list: a list of the paths to python packages containing schemas (a schema.json)
        """
        self.execution_folder = execution_folder

        self.logger = logging.getLogger("topology")

        if self.execution_folder:
            os.makedirs(self.execution_folder, exist_ok=True)

        self.schema = Schema()
        for package in package_list:
            self.schema.load_package(package)

        self.network = Network(self.schema, self.execution_folder)

        # the empty flag indicates that the topology contains no nodes and no
        # package properties or package data has been assigned
        self.empty = True

        # track which runners have been opened and are not yet closed
        self.read_only_runners = set()
        self.read_write_runners = set()  # at most 1

    def get_schema(self):
        return self.schema

    def load_zip(self, from_file: io.BytesIO, include_data: bool = True, include_configuration=True,
                 include_metadata=True) -> tuple[list[str], list[str], dict[str, str]]:
        """
        Load a topology from a binary stream

        Args:
            from_file: a binary stream, opened for reading
            include_data: whether or not to include the data from the file
            include_configuration: whether or not to include the configuration data and properties
            include_metadata: whether or not to include topology metadata

        Returns:
            a tuple containing the set of added node ids, the set of added link ids, and
            a dictionary containing any node renamings performed to avoid id collisions with existing nodes
        """
        (added_node_ids, added_link_ids, node_renamings) = self.network.load_zip(from_file,
                                                                                 include_configuration=include_configuration,
                                                                                 include_metadata=include_metadata,
                                                                                 include_data=include_data)
        return (added_node_ids, added_link_ids, node_renamings)

    def load_dir(self):
        """
        Load a topology from the execution folder
        """
        (added_node_ids, added_link_ids, node_renamings) = self.network.load_dir()

    def save_zip(self, to_file: io.BufferedWriter = None, include_data: bool = True) -> Union[None, bytes]:
        """
        Save a topology to a binary stream

        Args:
            to_file: an opened binary file to which the topology will be saved, if provided
            include_data: whether to include node/configuration data in the saved zip

        Returns:
            if to_file is not provided, returns a bytes object containing the saved topology
        """
        return self.network.save_zip(to_file, include_data=include_data)

    def import_from(self, from_path: str, include_data: bool = True, include_configuration: bool = False,
                    include_metadata: bool = False) -> tuple[list[str], list[str], dict[str, str]]:
        """
        Load the topology from a YAML file

        Args:
            from_path: the path tp a YAML file describing the topology
            include_data: whether or not to include any data referenced in the YAML file

        Returns:
            a tuple containing the set of added node ids, the set of added link ids, and
            a dictionary containing any node renamings performed to avoid id collisions with existing nodes
        """
        from hyrrokkin.utils.yaml_importer import import_from_yaml
        return import_from_yaml(self, from_path, include_data=include_data, include_configuration=include_configuration,
                                include_metadata=include_metadata)

    def export_to(self, to_path: str, include_data: bool = True):
        """
        save the topology to a zip file

        Args:
            to_path: the path to the YAML file to export to
            include_data: whether or not to export data to files that are referenced by the YAML
        """
        from hyrrokkin.utils.yaml_exporter import export_to_yaml
        export_to_yaml(self, to_path, include_data)

    def open_runner(self, execution_folder: str = None,
                    status_event_handler: Callable[[str, str, str, str], None] = None,
                    execution_event_handler: Callable[
                        [Union[float, None], str, str, Union[Dict, Exception, None], bool], None] = None,
                    engine_launcher: Union[EngineLauncher, None] = None,
                    read_only: bool = False, paused: bool = True,
                    set_engine_pid_callback=None) -> TopologyRunner:
        """
        Create a runner to run the topology

        Args:
            execution_folder: path to a folder in which the executor runs
            status_event_handler: specify a function to call when a node/configuration sets its status
                                 passing parameters target_id, target_type, msg, status
            execution_event_handler: specify a function to call when a node changes its execution status
                                passing parameters timestamp, node_id, state, exception, is_manual
            engine_launcher: the engine_launcher to use to run the topology in a remote process.  if not specified, select an appropriate one
                             for the packages loaded
            read_only: if true, do not allow nodes and configurations to persist data/properties changes to disk when running the topology
            paused: if true, start the runner in a paused state
            set_engine_pid_callback: function that is called with the process identifier (PID) of the engine process if the engine is launched in a sub-process


        Returns: a TopologyRunner instance that allows the execution to be stopped and clients to be attached and detached
        """

        if len(self.read_write_runners) > 0:
            raise ValueError("An open runner with read-write access exists")

        if not read_only:
            if len(self.read_only_runners) > 0:
                raise ValueError("Open runner(s) with read-only access exists")

        runner = TopologyRunner(network=self.network, schema=self.schema, execution_folder=execution_folder,
                                engine_launcher=engine_launcher, status_event_handler=status_event_handler,
                                execution_event_handler=execution_event_handler, read_only=read_only, paused=paused,
                                set_engine_pid_handler=set_engine_pid_callback)

        if read_only:
            self.read_only_runners.add(runner)
            runner.set_close_callback(lambda: self.read_only_runners.remove(runner))
        else:
            self.read_write_runners.add(runner)
            runner.set_close_callback(lambda: self.read_write_runners.remove(runner))

        return runner

    def set_metadata(self, metadata: dict[str, str]):
        """
        Set metadata for this topology

        Args:
            metadata: a dictionary containing metadata, consisting of string keys and values.

        Notes:
            the following keys will be understood by hyrrokkin based tools - version, description, authors
        """
        self.network.set_metadata(metadata)

    def add_node(self, node_id: str | None, node_type: str, metadata: dict[str, JsonType] = {},
                 properties: dict[str, JsonType] = {},
                 data: dict[str, bytes] = {}, copy_from_node_id: str = "") -> str:
        """
        Add a node to the topology

        Args:
            node_id: the requested node's unique identifier, must not already exist within the topology
            node_type: the type of the node, a string of the form package_id:node_type_id
            metadata: a dictionary containing the new metadata
            properties: dictionary containing the node's property names and values, must be JSON serialisable
            data: if set, initialise with the properties and data copied from this node
            copy_from_node_id: if set, initialise with the properties and data copied from this node rather than supplied in the data and properties arguments

        Returns:
              the node_id that was added, may be different to the requested identifier
        """
        if node_id is None or node_id == "" or self.network.get_node(node_id) is not None:
            node_id = self.network.create_node_id(node_type.split(":")[1])

        node = Node(node_id, node_type, metadata=metadata)
        if not copy_from_node_id:
            dsu = self.network.get_node_datastore(node_id)
            dsu.set_properties(properties)
            for key, value in data.items():
                dsu.set_data(key, value)
        self.network.add_node(node, copy_from_node_id=copy_from_node_id)

        return node_id

    def remove_node(self, node_id: str):
        """
        Remove a node from the topology

        Args:
            node_id: the node's unique identifier
        """
        if self.network.get_node(node_id) is None:
            raise InvalidNodeError(f"Node with id {node_id} does not exist")
        self.network.remove_node(node_id)

    def get_node_properties(self, node_id: str) -> dict[str, JsonType]:
        """
        Gets the properties of a node

        Args:
            node_id: the node's identifier

        Returns:
            dictionary containing properties
        """
        dsu = self.network.get_node_datastore(node_id)
        return dsu.get_properties()

    def set_node_properties(self, node_id: str, properties: dict[str, JsonType]):
        """
        Update the property of a node

        Args:
            node_id: the node's identifier
            properties: dictionary containing properties
        """
        dsu = self.network.get_node_datastore(node_id)
        dsu.set_properties(properties)

    def get_node_data(self, node_id: str, key: str) -> Union[bytes, None]:
        """
        Get binary data associated with this node.

        Args:
            node_id: node identifier
            key: a key to locate the data (can only contain alphanumeric characters and underscores)

        Returns:
            data or None if no data is associated with the key
        """
        dsu = self.network.get_node_datastore(node_id)
        return dsu.get_data(key)

    def set_node_data(self, node_id: str, key: str, data: Union[bytes, None]):
        """
        Set binary data associated with this node.

        Args:
            node_id: node identifier
            key: a key to locate the data (can only contain alphanumeric characters and underscores)
            data: data to be stored
        """
        dsu = self.network.get_node_datastore(node_id)
        dsu.set_data(key, data)

    def get_node_data_keys(self, node_id: str) -> list[str]:
        """
        Get the list of keys for which the node stores binary data

        Args:
            node_id: node identifier

        Returns:
            a set of data keys
        """
        dsu = self.network.get_node_datastore(node_id)
        return dsu.get_data_keys()

    def get_configuration_properties(self, package_id: str) -> dict[str, JsonType]:
        """
        Gets the properties package configuration

        Args:
            package_id: the package's identifier

        Returns:
            dictionary containing properties
        """
        dsu = self.network.get_configuration_datastore(package_id)
        return dsu.get_properties()

    def set_configuration_properties(self, package_id: str, properties: dict):
        """
        Set the properties of a package's configuration

        Args:
            package_id: the id of the package
            properties: a dictionary containing the configuration properties, must be JSON serialisable.
        """
        dsu = self.network.get_configuration_datastore(package_id)
        dsu.set_properties(properties)

    def get_configuration_data(self, package_id: str, key: str) -> Union[bytes, str, None]:
        """
        Get binary or string data associated with a package configuration.

        Args:
            package_id: package identifier
            key: a key to locate the data (can only contain alphanumeric characters and underscores)

        Returns:
            data or None if no data is associated with the key
        """
        dsu = self.network.get_configuration_datastore(package_id)
        return dsu.get_data(key)

    def set_configuration_data(self, package_id: str, key: str, data: Union[bytes, str, None]):
        """
        Set binary or string data associated with this node.

        Args:
            package_id: package identifier
            key: a key to locate the data (can only contain alphanumeric characters and underscores)
            data: data to be stored
        """
        dsu = self.network.get_configuration_datastore(package_id)
        dsu.set_data(key, data)
        self.empty = False

    def get_configuration_data_keys(self, package_id: str) -> list[str]:
        """
        Get the list of keys for which the package configuration stores binary data

        Args:
            package_id: package identifier

        Returns:
            a set of data keys
        """
        dsu = self.network.get_configuration_datastore(package_id)
        return dsu.get_data_keys()

    def add_link(self, link_id: str | None, from_node_id: str, from_port: Union[str, None], to_node_id: str,
                 to_port: Union[str, None]):
        """
        Add a link to the topology

        Args:
            link_id: the requested unique identifier for the link, may be None
            from_node_id: node id of the source node
            from_port: port name on the source node, can be omitted if the "from" node has only one output port
            to_node_id: node id of the destination node
            to_port: port name on the destination node, can be ommitted if the "to" node has only one input port

        Raises:
            InvalidLinkError: if the link cannot be added

        Returns:
            The link_id that was added
        """

        if link_id is None or link_id == "" or self.network.get_link(link_id) is not None:
            link_id = self.network.create_link_id()

        from_node = self.network.get_node(from_node_id)
        if from_node is None:
            raise InvalidLinkError(f"{from_node_id} does not exist")

        from_node_type_name = from_node.get_node_type()
        from_node_type = self.schema.get_node_type(from_node_type_name)

        to_node = self.network.get_node(to_node_id)
        if to_node is None:
            raise InvalidLinkError(f"{to_node_id} does not exist")
        to_node_type_name = to_node.get_node_type()
        to_node_type = self.schema.get_node_type(to_node_type_name)

        if from_port is None:
            if len(from_node_type.output_ports) == 1:
                from_port = next(iter(from_node_type.output_ports))
            else:
                output_port_names = ",".join(list(from_node_type.output_ports.keys()))
                raise InvalidLinkError(f"from_port not specified for link, should be one of ({output_port_names})")
        else:
            if from_port not in from_node_type.output_ports:
                raise InvalidLinkError(f"{from_port} is not a valid output port for node {from_node_id}")

        if to_port is None:
            if len(to_node_type.input_ports) == 1:
                to_port = next(iter(to_node_type.input_ports))
            else:
                input_port_names = ",".join(list(to_node_type.input_ports.keys()))
                raise InvalidLinkError(f"to_port not specified for link, should be one of ({input_port_names})")
        else:
            if to_port not in to_node_type.input_ports:
                raise InvalidLinkError(f"{to_port} is not a valid output port for node {to_node_id}")

        from_link_type = from_node_type.output_ports[from_port].link_type

        to_link_type = to_node_type.input_ports[to_port].link_type

        if from_link_type != to_link_type:
            raise InvalidLinkError(f"incompatible link types (from: {from_link_type}, to: {to_link_type})")

        if not from_node_type.output_ports[from_port].allows_multiple_connections():
            if len(self.network.get_outputs_from(from_node_id, from_port)) > 0:
                raise InvalidLinkError(
                    f"output port {from_node_id}/{from_port} is already connected and does not allow multiple connections")

        if not to_node_type.input_ports[to_port].allows_multiple_connections():
            if len(self.network.get_inputs_to(to_node_id, to_port)) > 0:
                raise InvalidLinkError(
                    f"input port {to_node_id}/{to_port} is already connected and does not allow multiple connections")

        link = Link(link_id, from_node_id, from_port, to_node_id, to_port, from_link_type)
        self.network.add_link(link)
        return link_id

    def remove_link(self, link_id: str):
        """
        Remove a link from the topology

        Args:
            link_id: the link's unique identifier
        """
        if self.network.get_link(link_id) is None:
            raise InvalidNodeError(f"Link with id {link_id} does not exist")
        else:
            self.network.remove_link(link_id)

    def get_package_ids(self) -> list[str]:
        """
        Gets the ids of all packages

        Returns:
             list of package ids
        """
        return list(self.schema.get_packages().keys())

    def get_node_ids(self) -> list[str]:
        """
        Get the ids of all nodes in the topology

        Returns:
            list of node ids
        """
        return self.network.get_node_ids()

    def get_node_type(self, node_id: str) -> tuple[str, str]:
        """
        Get the node package and type for a given node

        Args:
            node_id: the id of the node to retrieve

        Returns:
            tuple (package_id, node_type_id)
        """
        node = self.network.get_node(node_id)
        node_type = node.get_node_type()
        return self.schema.split_descriptor(node_type)

    def serialise_node(self, node_id: str) -> dict[str, JsonType]:
        """
        Serialise a node to a dictionary with self-explanatory keys

        Args:
            node_id: the id of the node to serialise

        Returns:
            a dictionary describing the node
        """
        node = self.network.get_node(node_id)
        d = {}
        d["node_id"] = node_id
        d["node_type"] = node.get_node_type()
        (x, y) = node.get_xy()
        d["x"] = x
        d["y"] = y
        d["metadata"] = node.get_metadata()
        return d

    def serialise_link(self, link_id: str) -> dict[str, JsonType]:
        """
        Serialise a link to a dictionary with self-explanatory keys

        Args:
            link_id: the id of the link to serialise

        Returns:
            a dictionary describing the link
        """
        link = self.network.get_link(link_id)
        msg = {}
        msg["link_id"] = link_id
        msg["link_type"] = link.get_link_type()
        msg["from_node"] = link.from_node_id
        msg["from_port"] = link.from_port
        msg["to_node"] = link.to_node_id
        msg["to_port"] = link.to_port
        return msg

    def serialise(self) -> dict[str, JsonType]:
        """
        Serialise the topology to a dictionary without data/properties

        Returns:
            a dictionary describing the topoology
        """

        return self.network.save()

    def get_node_metadata(self, node_id: str) -> dict[str, JsonType]:
        """
        Get the metadata of a node

        Args:
            node_id: the id of the node

        Returns:
            A dictionary containing the metadata
        """
        return self.network.get_node(node_id).get_metadata()

    def update_node_metadata(self, node_id: str, metadata: dict[str, JsonType]):
        """
        Updates the metadata of a node

        Args:
            node_id: the id of the node
            metadata: a dictionary containing the new metadata
        """
        self.network.update_node_metadata(node_id, metadata)

    def get_link_ids(self) -> list[str]:
        """
        Get the ids of all links in the topology

        Returns:
            list of link ids
        """
        return self.network.get_link_ids()

    def get_link_ids_for_node(self, node_id: str) -> list[str]:
        """
        Get the ids of all links in the topology that are connected to a node

        Args:
            node_id: the id of the node

        Returns:
            list of link ids connected to the node
        """
        return self.network.get_link_ids_for_node(node_id)

    def get_link(self, link_id: str) -> tuple[str, str, str, str]:
        """
        Get the link details for a given link

        Args:
            link_id: the id of the link to retrieve

        Returns:
            tuple (from_node_id,from_port,to_node_id,to_port)
        """
        link = self.network.get_link(link_id)
        return (link.from_node_id, link.from_port, link.to_node_id, link.to_port)

    def get_link_type(self, link_id: str) -> str:
        """
        Gets the link_type for a given link

        Args:
            link_id: the id of the link
        """
        link = self.network.get_link(link_id)
        return link.get_link_type()

    def get_output_port_names(self, node_id: str) -> list[str]:
        """
        Get the output port names for a given node

        Args:
            node_id: the id of the node

        Returns:
            list of output port names
        """
        node = self.network.get_node(node_id)
        node_type = self.schema.get_node_type(node.get_node_type())
        return [name for (name, _) in node_type.get_output_ports()]

    def get_input_port_names(self, node_id: str) -> list[str]:
        """
        Get the input port names for a given node

        Args:
            node_id: the id of the node

        Returns:
            list of input port names
        """
        node = self.network.get_node(node_id)
        node_type = self.schema.get_node_type(node.get_node_type())
        return [name for (name, _) in node_type.get_input_ports()]

    def get_metadata(self) -> dict[str, JsonType]:
        """
        Get the metadata of the topology

        Returns:
            A dictionary containing the metadata
        """
        return self.network.get_metadata()

    def get_nodes(self):
        nodes = {}
        for node_id in self.network.get_node_ids():
            node = self.network.get_node(node_id)
            nodes[node_id] = node
        return nodes

    def get_links(self):
        links = {}
        for link_id in self.network.get_link_ids():
            link = self.network.get_link(link_id)
            links[link_id] = link
        return links

    def get_node_properties(self, node_id: str) -> dict[str, JsonType]:
        """
        Get the properties for the specified node

        Args:
            node_id: the node identifier

        Returns:
            A dictionary containing the properties defined for that node
        """
        dsu = self.network.get_node_datastore(node_id)
        return dsu.get_properties()

    def get_configuration_properties(self, package_id: str) -> dict[str, JsonType]:
        """
        Get the properties for the specified package configuration

        Args:
            package_id: the package identifier

        Returns:
            A dictionary containing the properties defined for that package configuration
        """
        dsu = self.network.get_configuration_datastore(package_id)
        return dsu.get_properties()

    def clear(self):
        """
        Remove all nodes and links from the topology
        """
        self.network.clear()

    def get_localisation_bundle(self, package_id, for_language=""):
        return self.schema.get_localisation_bundle(package_id=package_id,for_language=for_language)
