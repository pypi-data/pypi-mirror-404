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

from abc import abstractmethod, ABC
from typing import Callable, Tuple, Any
import io

from hyrrokkin.interfaces.topology_listener_api import TopologyListenerAPI
from hyrrokkin.interfaces.client_api import ClientApi
from hyrrokkin.interfaces.schema_api import SchemaTypeApi, NodeTypeApi, LinkTypeApi
from hyrrokkin.utils.type_hints import JsonType


class TopologyApi(ABC):

    @abstractmethod
    def set_metadata(self, metadata: dict[str, str], ref: str | None = None):
        """
        Set metadata for this topology

        Args:
            metadata: a dictionary containing metadata, consisting of string keys and values.
            ref: an optional reference that identifies this request

        Notes:
            the following keys will be understood by hyrrokkin based tools - version, description, authors
        """

    @abstractmethod
    def add_node(self, node_id: str | None, node_type: str, metadata: dict[str, JsonType] = {},
                 properties: dict[str, JsonType] = {},
                 data: dict[str, bytes] = {}, copy_from_node_id: str = "", ref: str | None = None) -> str:
        """
        Add a node to the topology

        Args:
            node_id: the node's requested unique identifier or None
            node_type: the type of the node, a string of the form package_id:node_type_id
            metadata: a dictionary containing the new metadata
            properties: dictionary containing the node's property names and values, must be JSON serialisable
            data: if set, initialise with the properties and data copied from this node
            copy_from_node_id: if set, initialise with the properties and data copied from this node rather than supplied in the data and properties arguments
            ref: an optional reference that identifies this request

        Returns:
            the id of the added node
        """

    @abstractmethod
    def update_node_metadata(self, node_id: str | None, metadata: dict[str, JsonType] = {},
                             ref: str | None = None) -> None:
        """
        Update a node's metadata

        Args:
            node_id: the node's requested unique identifier or None
            metadata: a dictionary containing the new metadata
            ref: an optional reference that identifies this request
        """

    @abstractmethod
    def remove_node(self, node_id: str, ref: str | None = None):
        """
        Remove a node from the topology

        Args:
            node_id: the node's unique identifier
            ref: an optional reference that identifies this request
        """

    @abstractmethod
    def add_link(self, link_id: str, from_node_id: str, from_port: str | None, to_node_id: str,
                 to_port: str | None, ref: str | None = None) -> str:
        """
        Add a link to the topology

        Args:
            link_id: a requested unique identifier for the link
            from_node_id: node id of the source node
            from_port: port name on the source node, can be omitted if the "from" node has only one output port
            to_node_id: node id of the destination node
            to_port: port name on the destination node, can be omitted if the "to" node has only one input port
            ref: an optional reference that identifies this request

        Raises:
            InvalidLinkError: if the link cannot be added

        Returns:
            link_id of the added link
        """

    def remove_link(self, link_id: str, ref: str | None = None):
        """
        Remove a link from the topology

        Args:
            link_id: the link's unique identifier
            ref: an optional reference that identifies this request

        """

    @abstractmethod
    def clear(self, ref: str | None = None):
        """
        Remove all nodes and links from the topology

        Args:
            ref: an optional reference that identifies this request

        """

    @abstractmethod
    def start(self, ref: str | None = None):
        """
        Start execution of the topology

        Args:
            ref: an optional reference that identifies this request
        """

    @abstractmethod
    def is_started(self):
        """
        Returns: True if the topology is executing
        """

    @abstractmethod
    def pause(self, ref: str | None = None):
        """
        Pause execution of the topology.  Until resume is called, no new nodes will start running.

        Args:
            ref: an optional reference that identifies this request
        """

    @abstractmethod
    def resume(self, ref: str | None = None):
        """
        Resume execution of the topology

        Args:
            ref: an optional reference that identifies this request
        """

    @abstractmethod
    def is_paused(self):
        """
        Returns: True if the topology is paused
        """

    @abstractmethod
    def restart(self, ref: str | None = None):
        """

        Restart execution of the topology

        Args:
            ref: an optional reference that identifies this request

        """

    @abstractmethod
    def run(self) -> dict[str, str]:
        """

        Run the topology until all nodes have completed or failed

        Returns: a dictionary containing the error messages returned from any failed nodes
        """

    @abstractmethod
    def run_task(self, task_name: str, input_port_values:dict[str,bytes|list[bytes]], output_ports:list[str], ref: str | None = None, decode_outputs:bool = True) -> tuple[
        dict[str, bytes], dict[str, str]]:
        """
        Run a topology task

        Args:
            task_name: a descriptive name of the task
            input_port_values: map from port identifier (node_id:input_port_name) to a binary-encoded input value or list of values
            output_ports: a list of port identifiers (node_id:output_port_name) specifying output ports to return values from
            ref: an optional reference that identifies this request
            decode_outputs: whether to decode output values from binary or return the binary values

        Returns:
            return a tuple of (dict mapping from output port name to value, dict mapping from node id to error string)
        """

    @abstractmethod
    def reload_node(self, node_id: str, properties: JsonType, data: dict[str, bytes], ref: str | None = None):
        """
        Reload a node with new properties and data, triggering re-execution of the node and all downstream nodes
        if the topology execution has already started

        Reloading creates a new instance of the node with the new properties and data

        Args:
            node_id: the id of the node to reload
            properties: the properties to reload
            data: the data to reload
            ref: an optional reference that identifies this request
        """

    ####################################################################################################################
    # retrieve node properties and data

    @abstractmethod
    def get_node_properties(self, node_id: str) -> dict[str, JsonType]:
        """
        Gets the properties of a node

        Args:
            node_id: the node's identifier

        Returns:
            dictionary containing properties
        """

    @abstractmethod
    def get_node_data(self, node_id: str, key: str) -> bytes | None:
        """
        Get binary data associated with this node.

        Args:
            node_id: node identifier
            key: a key to locate the data (can only contain alphanumeric characters and underscores)

        Returns:
            data or None if no data is associated with the key
        """

    @abstractmethod
    def get_node_data_keys(self, node_id: str) -> list[str]:
        """
        Get the list of keys for which the node stores binary data

        Args:
            node_id: node identifier

        Returns:
            a set of data keys
        """

    ####################################################################################################################
    # interact with the topology

    @abstractmethod
    def add_output_listener(self, node_id: str, output_port_name: str, listener: Callable[[Any], None], decode_outputs:bool = True):
        """
        Listen for values output from a node in the topology.  Replaces any existing listener on the node/port if present.

        Args:
            node_id: the node id
            output_port_name: the name of the node's output port
            listener: a callback function which is invoked with the value(s) on the output port when the node is run
            decode_outputs: if True, decode output values from binary, otherwise return the binary values
        """

    @abstractmethod
    def remove_output_listener(self, node_id: str, output_port_name: str):
        """
        Remove a listener from a node/port

        Args:
            node_id: the node id
            output_port_name: the name of the node's output port
        """

    @abstractmethod
    def inject_input_value(self, node_id: str, input_port_name: str, value: Any):
        """
        Inject input values into a node in the topology, via an input port.  The port must not be connected.

        Args:
            node_id: the node id
            input_port_name: the name of the node's input port
            value: the value to inject
        """

    @abstractmethod
    def inject_input_values(self, node_id: str, input_port_name: str, values: list[Any]):
        """
        Inject input values into a node in the topology, via an input port.  The port must not be connected and must allow multiple input connections.

        Args:
            node_id: the node id
            input_port_name: the name of the node's input port
            values: the values to inject.
        """

    ####################################################################################################################
    # session and client related

    @abstractmethod
    def open_session(self, session_id: str | None = None) -> str:
        """
        Open a new interactive session

        Args:
            session_id: the identifier of the session or None to generate a new session identifier

        Returns:
            the session identifier for the opened session
        """

    @abstractmethod
    def close_session(self, session_id: str):
        """
        Close a session

        Args:
            session_id: the identifier of the session to close
        """

    @abstractmethod
    def attach_node_client(self, node_id: str, session_id: str = "", client_id: str = "",
                           client_options: dict = {}) -> ClientApi:
        """
        Attach a client instance to a node.  Any client already attached to the node with the same client_id
        will be detached.

        Args:
            node_id: the node to which the client is to be attached
            session_id: the id of an opened interactive session
            client_id: the name of the client to attach, as defined in the node's schema
            client_options: optional, a dictionary with extra parameters from the client

        Returns:
             an instance which implements the Client API and provides methods to interact with the node

        """

    @abstractmethod
    def attach_configuration_client(self, package_id: str, session_id: str = "", client_id: str = "",
                                    client_options: dict = {}) -> ClientApi:
        """
        Attach a client instance to a package configuration

        Args:
            package_id: the package configuration to which the client is to be attached
            session_id: the id of an opened interactive session
            client_id: the id of the client to attach
            client_options: optional, a dictionary with extra parameters for the client

        Returns:
             an object which implements the Client API and provides methods to interact with the configuration
        """

    ####################################################################################################################
    # load and save

    @abstractmethod
    def load(self, from_file: io.BytesIO, include_data: bool = True, ref: str | None = None) -> Tuple[
        list[str], list[str], dict[str, str]]:
        """
        Merge the nodes and links topology from an opened ZIP file into this topology.  Node and link ids will be renamed to avoid clashes.

        Args:
            from_file: a file opened in binary mode
            include_data: whether or not to include the data from the file

        Returns:
            a tuple containing the set of added node ids, the set of added link ids, and
            a dictionary containing any node renamings performed to avoid id collisions with existing nodes
            ref: an optional reference that identifies this request

        Notes:
            configuration properties/data will not be loaded if this method is called after the topology is started
            topology metadata will not be loaded if topology metadata already exists
        """

    @abstractmethod
    def save(self, to_file: io.BufferedWriter = None, include_data: bool = True):
        """
        save the topology to a zip file

        Args:
            to_file: a file opened in binary mode for writing
            include_data: whether or not to include the data in the file
        """

    @abstractmethod
    def serialise(self):
        """
        Serialise the topology structure to JSON

        Returns: JSON-serialisable dictionary

        """

    @abstractmethod
    def import_from(self, from_path: str, include_data: bool = True, ref: str | None = None) -> Tuple[
        list[str], list[str], dict[str, str]]:
        """
        Merge the nodes and links topology from a YAML file or ZIP file into this topology.  Node and link ids will be renamed to avoid clashes.

        Args:
            from_path: the path to a YAML or ZIP file describing the topology
            include_data: whether or not to include any data referenced in the YAML file
            ref: an optional reference that identifies this request

        Returns:
            a tuple containing the set of added node ids, the set of added link ids, and
            a dictionary containing any node renamings performed to avoid id collisions with existing nodes

        Notes:
            configuration properties/data will not be loaded if this method is called after the topology is started
            topology metadata will not be loaded if topology metadata already exists
        """

    @abstractmethod
    def export_to(self, to_path: str, include_data: bool = True):
        """
        save the topology to a zip file or yaml file

        Args:
            to_path: the path to the YAML file or ZIP file to export to
            include_data: whether or not to export data as well as properties
        """

    ####################################################################################################################
    # topology introspection

    @abstractmethod
    def get_nodes(self) -> dict[str, NodeTypeApi]:
        """
        Get details of the node ids and types in the topology

        Returns:
            dict containing a mapping from node id to node type
        """

    @abstractmethod
    def get_links(self) -> dict[str, tuple[LinkTypeApi, str, str]]:
        """
        Get details of the link ids and link types in the topology

        Returns:
            dict containing a mapping from link id to a tuple of format (link_type,<node_id>:<from_port_name>,<node_id>:<to_port_name>)>
        """

    @abstractmethod
    def get_link_ids_for_node(self, node_id: str) -> list[str]:
        """
        Get the ids of all links in the topology that are connected to a node

        Args:
            node_id: the id of the node

        Returns:
            list of link ids connected to the node
        """

    ####################################################################################################################
    # schema introspection

    def get_schema(self) -> SchemaTypeApi:
        """

        Returns: an instance implementing the SchemaApi allowing the packahes, node types and link types in the schema to be examined

        """

    ####################################################################################################################
    # Attach and Detach Listeners

    @abstractmethod
    def attach_listener(self, listener: TopologyListenerAPI) -> None:
        """
        Attach a listener instance which implements the TopologyListenerAPI

        Args:
            listener: the listener instance
        """

    @abstractmethod
    def detach_listener(self, listener: TopologyListenerAPI) -> None:
        """
        Detach a listener

        Args:
            listener: the listener instance
        """

    ####################################################################################################################
    # localisation

    def get_type_for_node(self, node_id:str) -> (str,str):
        """
        Get the package_id, node_type_id for a given node

        Args:
            node_id: the identifier of the node
        Returns:
             tuple containing package id and node type id
        """

    def get_localisation_bundle(self, package_id:str, for_language:str="") -> tuple[str,dict[str,str]]:
        """
        Get a localisation bundle for a package.  If the requested language is not available returns the default language code and bundle.

        Args:
            package_id: the package identifier
            for_language: specify the language, if not specified return the default language bundle

        Returns:
            a tuple with the language code and a dictionary containing the localisation bundle
        """
